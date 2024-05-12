import pandas as pd
from typing import Dict, Union, List, Optional


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

    normal_fq1: Optional[str]
    normal_fq2: Optional[str]
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
        self.set_normal_fq1_fq2()
        self.set_stdout()
        self.set_rsync_fastq_cmds()
        self.set_somatic_pipeline_cmd()
        self.set_rsync_output_cmd()
        self.set_rm_cmds()

        cmds = self.rsync_fastq_cmds + [self.somatic_pipeline_cmd] + [self.rsync_output_cmd] + self.rm_cmds

        return '   &&   \\\n'.join(cmds)

    def load_default_parameters(self):
        default = DEFAULT_COMPUTE_PARAMETERS.copy()
        default.update(DEFAULT_NAS_PARAMETERS)
        default.update(DEFAULT_PIPELINE_PARAMETERS)
        for key, values in default.items():
            if key not in self.parameters:
                if type(values) is bool:
                    self.parameters[key] = values
                else:  # list
                    self.parameters[key] = values[0]

    def set_normal_fq1_fq2(self):
        row = self.sample_row
        self.normal_fq1 = row.get('Normal Fastq R1', pd.NA)
        self.normal_fq2 = row.get('Normal Fastq R2', pd.NA)
        if pd.isna(self.normal_fq1):
            self.normal_fq1 = None
        if pd.isna(self.normal_fq2):
            self.normal_fq2 = None

    def set_stdout(self):
        outdir = self.sample_row['Output Name']
        self.stdout = f"2>&1 > '{outdir}/progress.txt'"

    def set_rsync_fastq_cmds(self):
        p = self.parameters
        row = self.sample_row

        user = p['NAS User']
        ip = p['NAS Local IP']
        port = p['NAS Port']
        srcdir = f"{p['NAS Sequencing Directory'].rstrip('/')}/{row['Sequencing Batch ID']}"
        tumor_fq1 = row['Tumor Fastq R1']
        tumor_fq2 = row['Tumor Fastq R2']

        self.rsync_fastq_cmds = [
            f"rsync -avz -e 'ssh -p {port}' {user}@{ip}:'{srcdir}/{tumor_fq1}' '{self.LOCAL_FASTQ_DIR}/' {self.stdout}",
            f"rsync -avz -e 'ssh -p {port}' {user}@{ip}:'{srcdir}/{tumor_fq2}' '{self.LOCAL_FASTQ_DIR}/' {self.stdout}",
        ]

        if self.normal_fq1 is not None:
            self.rsync_fastq_cmds += [
                f"rsync -avz -e 'ssh -p {port}' {user}@{ip}:'{srcdir}/{self.normal_fq1}' '{self.LOCAL_FASTQ_DIR}/' {self.stdout}",
                f"rsync -avz -e 'ssh -p {port}' {user}@{ip}:'{srcdir}/{self.normal_fq2}' '{self.LOCAL_FASTQ_DIR}/' {self.stdout}",
            ]

    def set_somatic_pipeline_cmd(self):
        p = self.parameters
        row = self.sample_row

        n1 = 'None' if self.normal_fq1 is None else f'{self.LOCAL_FASTQ_DIR}/{self.normal_fq1}'
        n2 = 'None' if self.normal_fq2 is None else f'{self.LOCAL_FASTQ_DIR}/{self.normal_fq2}'

        self.somatic_pipeline_cmd = f'''\
python {p['Somatic Pipeline']} main \\
--ref-fa='{p['ref-fa']}' \\
--tumor-fq1='{self.LOCAL_FASTQ_DIR}/{row['Tumor Fastq R1']}' \\
--tumor-fq2='{self.LOCAL_FASTQ_DIR}/{row['Tumor Fastq R2']}' \\
--normal-fq1='{n1}' \\
--normal-fq2='{n2}' \\
--outdir='{row['Output Name']}' \\
--threads={p['threads']} \\
--umi-length={p['umi-length']} \\
--clip-r1-5-prime={p['clip-r1-5-prime']} \\
--clip-r2-5-prime={p['clip-r2-5-prime']} \\
--read-aligner='{p['read-aligner']}' \\
{'--skip-mark-duplicates' if p['skip-mark-duplicates'] else ''} \\
--bqsr-known-variant-vcf='{p['bqsr-known-variant-vcf']}' \\
{'--discard-bam' if p['discard-bam'] else ''} \\
--variant-callers='{p['variant-callers']}' \\
{'--skip-variant-calling' if p['skip-variant-calling'] else ''} \\
--call-region-bed='{p['BED Directory'].rstrip('/')}/{row['BED File']}' \\
--panel-of-normal-vcf='{p['panel-of-normal-vcf']}' \\
--germline-resource-vcf='{p['germline-resource-vcf']}' \\
--variant-flagging-criteria='{p['variant-flagging-criteria']}' \\
--variant-removal-flags='{p['variant-removal-flags']}' \\
{'--only-pass' if p['only-pass'] else ''} \\
--min-snv-callers={p['min-snv-callers']} \\
--min-indel-callers={p['min-indel-callers']} \\
{'--skip-variant-annotation' if p['skip-variant-annotation'] else ''} \\
--vep-db-tar-gz='{p['vep-db-tar-gz']}' \\
--vep-db-type='{p['vep-db-type']}' \\
--vep-buffer-size={p['vep-buffer-size']} \\
{self.stdout}'''

    def set_rsync_output_cmd(self):
        p = self.parameters
        row = self.sample_row

        outdir = row['Output Name']
        user = p['NAS User']
        ip = p['NAS Local IP']
        port = p['NAS Port']
        dstdir = p['NAS Destination Directory'].rstrip('/')
        self.rsync_output_cmd = f"rsync -avz -e 'ssh -p {port}' '{outdir}' {user}@{ip}:'{dstdir}/'"

    def set_rm_cmds(self):
        row = self.sample_row

        self.rm_cmds = [
            f"rm -r '{row['Output Name']}'",
            f"rm '{self.LOCAL_FASTQ_DIR}/{row['Tumor Fastq R1']}'",
            f"rm '{self.LOCAL_FASTQ_DIR}/{row['Tumor Fastq R2']}'",
        ]

        if self.normal_fq1 is not None:
            self.rm_cmds += [
                f"rm '{self.LOCAL_FASTQ_DIR}/{self.normal_fq1}'",
                f"rm '{self.LOCAL_FASTQ_DIR}/{self.normal_fq2}'",
            ]


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
