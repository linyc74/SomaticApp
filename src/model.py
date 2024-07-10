import pandas as pd
from os.path import abspath, expanduser
from typing import Dict, Union, List


COMPUTE_ROOT_DIR = '~/SomaticApp'
COMPUTE_BASH_PROFILE = '~/SomaticApp/.bash_profile'
NAS_OUTPUT_ROOT_DIR = '~/SomaticApp'
DEFAULT_COMPUTE_PARAMETERS = {
    'Compute User': [''],
    'Compute Public IP': ['255.255.255.255'],
    'Compute Port': ['22'],
    'Somatic Pipeline': ['somatic_pipeline-1.0.0'],
    'BED Directory': ['resource/bed'],
}
DEFAULT_NAS_PARAMETERS = {
    'NAS User': [''],
    'NAS Local IP': ['255.255.255.255'],
    'NAS Port': ['22'],
    'NAS Sequencing Directory': [''],
    'NAS Destination Directory': [''],
}
DEFAULT_PIPELINE_PARAMETERS = {
    'ref-fa': ['resource/GRCh38.primary_assembly.genome.fa'],
    'threads': [4],
    'umi-length': [0],
    'clip-r1-5-prime': [0],
    'clip-r2-5-prime': [0],
    'read-aligner': ['bwa'],
    'skip-mark-duplicates': False,
    'bqsr-known-variant-vcf': ['None'],
    'discard-bam': False,
    'variant-callers': [
        'mutect2,muse,lofreq',
        'mutect2,muse,lofreq,vardict,varscan,somatic-sniper',
        'haplotype-caller',
    ],
    'skip-variant-calling': False,
    'panel-of-normal-vcf': ['None'],
    'germline-resource-vcf': ['None'],
    'variant-flagging-criteria': ['None'],
    'variant-removal-flags': ['None'],
    'only-pass': False,
    'min-snv-callers': [1],
    'min-indel-callers': [1],
    'skip-variant-annotation': False,
    'vep-db-tar-gz': ['None'],
    'vep-db-type': ['merged'],
    'vep-buffer-size': [5000],
}


class BuildSubmissionCommands:

    LOCAL_FASTQ_DIR = './fastq'

    run_table: str
    parameters: Dict[str, Union[str, int, bool]]

    commands: List[str]

    def main(
            self,
            run_table: str,
            parameters: Dict[str, Union[str, int]]) -> List[str]:

        self.run_table = run_table
        self.parameters = parameters.copy()

        self.commands = []
        for _, row in pd.read_csv(self.run_table).iterrows():

            script = BuildExecutionScript().main(
                parameters=self.parameters,
                sample_row=row)

            cmd = build_submit_cmd(
                job_name=row['Output Name'],
                outdir=row['Output Name'],
                script=script
            )

            self.commands.append(cmd)

        return self.commands


class BuildExecutionScript:

    LOCAL_FASTQ_DIR = './fastq'

    parameters: Dict[str, Union[str, int, bool]]
    sample_row: pd.Series

    stdout: str
    rsync_fastq_cmds: List[str]
    somatic_pipeline_cmd: str
    rsync_output_cmd: str
    rm_cmds: List[str]

    def main(
            self,
            parameters: Dict[str, Union[str, int, bool]],
            sample_row: pd.Series) -> str:

        self.parameters = parameters
        self.sample_row = sample_row

        self.load_default_parameters()
        self.set_stdout()
        self.set_rsync_fastq_cmds()
        self.set_somatic_pipeline_cmd()
        self.set_rsync_output_cmd()
        self.set_rm_cmds()

        cmds = self.rsync_fastq_cmds + [self.somatic_pipeline_cmd] + [self.rsync_output_cmd] + self.rm_cmds

        return '   &&   \\\n'.join(cmds)

    def load_default_parameters(self):
        for default in [
            DEFAULT_COMPUTE_PARAMETERS,
            DEFAULT_NAS_PARAMETERS,
            DEFAULT_PIPELINE_PARAMETERS
        ]:
            for key, values in default.items():
                if key not in self.parameters:
                    if type(values) is bool:
                        self.parameters[key] = values
                    else:  # list
                        self.parameters[key] = values[0]

    def set_stdout(self):
        outdir = self.sample_row['Output Name']
        self.stdout = f"2>&1 >> '{outdir}/progress.txt'"

    def set_rsync_fastq_cmds(self):
        p = self.parameters
        row = self.sample_row

        user = p['NAS User']
        ip = p['NAS Local IP']
        port = p['NAS Port']
        srcdir = f"{p['NAS Sequencing Directory'].rstrip('/')}/{row['Sequencing Batch ID']}"
        tumor_fq1 = row['Tumor Fastq R1']
        tumor_fq2 = row['Tumor Fastq R2']
        normal_fq1 = row.get('Normal Fastq R1', pd.NA)
        normal_fq2 = row.get('Normal Fastq R2', pd.NA)

        fqs = [tumor_fq1, tumor_fq2]
        if pd.notna(normal_fq1):
            fqs += [normal_fq1, normal_fq2]

        self.rsync_fastq_cmds = []
        for fq in fqs:
            self.rsync_fastq_cmds.append(
                f"rsync -avz -e 'ssh -p {port}' {user}@{ip}:'{srcdir}/{fq}' '{self.LOCAL_FASTQ_DIR}/' {self.stdout}"
            )

    def set_somatic_pipeline_cmd(self):
        p = self.parameters
        row = self.sample_row

        lines = [
            f"python {p['Somatic Pipeline']} main",
            f"--tumor-fq1='{self.LOCAL_FASTQ_DIR}/{row['Tumor Fastq R1']}'",
            f"--tumor-fq2='{self.LOCAL_FASTQ_DIR}/{row['Tumor Fastq R2']}'",
            f"--call-region-bed='{p['BED Directory'].rstrip('/')}/{row['BED File']}'",
            f"--outdir='{row['Output Name']}'",
        ]

        normal_fq1 = row.get('Normal Fastq R1', pd.NA)
        normal_fq2 = row.get('Normal Fastq R2', pd.NA)
        if pd.notna(normal_fq1):
            lines.append(f"--normal-fq1='{self.LOCAL_FASTQ_DIR}/{normal_fq1}'")
            lines.append(f"--normal-fq2='{self.LOCAL_FASTQ_DIR}/{normal_fq2}'")

        for key in DEFAULT_PIPELINE_PARAMETERS.keys():

            if key not in p:
                continue

            dtype = self.__get_type(key)

            if dtype is bool:
                if p[key]:
                    lines.append(f"--{key}")
            elif dtype is int:
                lines.append(f"--{key}={p[key]}")
            else:  # str
                lines.append(f"--{key}='{p[key]}'")

        lines.append(self.stdout)

        self.somatic_pipeline_cmd = ' \\\n'.join(lines)

    def __get_type(self, key: str) -> type:
        # type determined by default value, not by input value, which is always str
        values = DEFAULT_PIPELINE_PARAMETERS.get(key)
        if type(values) is bool:
            return bool
        return type(values[0])

    def set_rsync_output_cmd(self):
        p = self.parameters
        row = self.sample_row

        outdir = row['Output Name']
        user = p['NAS User']
        ip = p['NAS Local IP']
        port = p['NAS Port']
        dstdir = p['NAS Destination Directory'].lstrip('.').lstrip('/').rstrip('/')  # remove leading './' and trailing '/'

        if dstdir != '':
            dstdir += '/'

        if not is_subdir(parent=NAS_OUTPUT_ROOT_DIR, child=f'{NAS_OUTPUT_ROOT_DIR}/{dstdir}'):
            raise ValueError(f"Destination directory '{NAS_OUTPUT_ROOT_DIR}/{dstdir}' is not a subdirectory of NAS root directory '{NAS_OUTPUT_ROOT_DIR}'")

        self.rsync_output_cmd = f"rsync -avz -e 'ssh -p {port}' '{outdir}' {user}@{ip}:'{NAS_OUTPUT_ROOT_DIR}/{dstdir}'"

    def set_rm_cmds(self):
        row = self.sample_row

        self.rm_cmds = [f"rm -r '{row['Output Name']}'"]

        tumor_fq1 = row['Tumor Fastq R1']
        tumor_fq2 = row['Tumor Fastq R2']
        normal_fq1 = row.get('Normal Fastq R1', pd.NA)
        normal_fq2 = row.get('Normal Fastq R2', pd.NA)

        fqs = [tumor_fq1, tumor_fq2]
        if pd.notna(normal_fq1):
            fqs += [normal_fq1, normal_fq2]

        for fq in fqs:
            self.rm_cmds.append(f"rm '{self.LOCAL_FASTQ_DIR}/{fq}'")


def is_subdir(parent: str, child: str) -> bool:
    p = abspath(expanduser(parent))
    c = abspath(expanduser(child))
    return c.startswith(p)


def build_submit_cmd(
        job_name: str,
        outdir: str,
        script: str) -> str:

    outdir = outdir.rstrip('/')
    cmd_txt = f'{outdir}/commands.txt'

    cmd = f'''\
mkdir -p "{outdir}"   &&   \\
echo "{script}" > "{cmd_txt}"   &&   \\
screen -S {job_name} -dm bash "{cmd_txt}"
'''

    return cmd
