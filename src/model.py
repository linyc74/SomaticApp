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
    'ref-fa': [''],
    'threads': [4],
    'umi-length': [0],
    'clip-r1-5-prime': [0],
    'clip-r2-5-prime': [0],
    'read-aligner': ['bwa'],
    'skip-mark-duplicates': False,
    'bqsr-known-variant-vcf': [''],
    'discard-bam': False,
    'variant-callers': ['mutect2,muse,lofreq'],
    'skip-variant-calling': False,
    'panel-of-normal-vcf': [''],
    'germline-resource-vcf': [''],
    'variant-flagging-criteria': ['None'],
    'variant-removal-flags': ['None'],
    'only-pass': False,
    'min-snv-callers': [1],
    'min-indel-callers': [1],
    'skip-variant-annotation': False,
    'vep-db-tar-gz': [''],
    'vep-db-type': ['merge'],
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

        self.load_default_parameters()

        self.commands = []
        for _, row in pd.read_csv(self.run_table).iterrows():
            self.build_one_command(row=row)

        return self.commands

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

    def build_one_command(self, row: pd.Series):
        p = self.parameters

        nas_fastq_dir = f"{p['NAS Sequencing Directory'].rstrip('/')}/{row['Sequencing Batch ID']}"
        call_region_bed = f"{p['BED Directory'].rstrip('/')}/{row['BED File']}"

        normal_fq1 = row.get('Normal Fastq R1', pd.NA)
        normal_fq2 = row.get('Normal Fastq R2', pd.NA)
        if pd.isna(normal_fq1):
            normal_fq1 = None
        if pd.isna(normal_fq2):
            normal_fq2 = None

        script = build_execution_script(
            nas_user=p['NAS User'],
            nas_ip=p['NAS Local IP'],
            nas_port=p['NAS Port'],
            nas_fastq_dir=nas_fastq_dir,
            nas_dst_dir=p['NAS Destination Directory'],
            tumor_fq1=row['Tumor Fastq R1'],
            tumor_fq2=row['Tumor Fastq R2'],
            normal_fq1=normal_fq1,
            normal_fq2=normal_fq2,
            local_fastq_dir=self.LOCAL_FASTQ_DIR,
            somatic_pipeline=p['Somatic Pipeline'],
            ref_fa=p['ref-fa'],
            outdir=row['Output Name'],
            threads=p['threads'],
            umi_length=p['umi-length'],
            read_aligner=p['read-aligner'],
            bqsr_known_variant_vcf=p['bqsr-known-variant-vcf'],
            variant_callers=p['variant-callers'],
            min_snv_callers=p['min-snv-callers'],
            min_indel_callers=p['min-indel-callers'],
            panel_of_normal_vcf=p['panel-of-normal-vcf'],
            call_region_bed=call_region_bed,
            variant_removal_flags=p['variant-removal-flags'],
            vep_db_tar_gz=p['vep-db-tar-gz'],
            vep_db_type=p['vep-db-type'],
            vep_buffer_size=p['vep-buffer-size'],
        )

        cmd = build_submit_cmd(
            job_name=row['Output Name'],
            outdir=row['Output Name'],
            script=script
        )

        self.commands.append(cmd)


def build_execution_script(
        nas_user: str,
        nas_ip: str,
        nas_port: int,
        nas_fastq_dir: str,
        nas_dst_dir: str,
        tumor_fq1: str,
        tumor_fq2: str,
        normal_fq1: Optional[str],
        normal_fq2: Optional[str],
        local_fastq_dir: str,
        somatic_pipeline: str,
        ref_fa: str,
        outdir: str,
        threads: int = 4,
        umi_length: int = 0,
        clip_r1_5_prime: int = 0,
        clip_r2_5_prime: int = 0,
        read_aligner: str = 'bwa',
        skip_mark_duplicates: bool = False,
        bqsr_known_variant_vcf: str = 'None',
        discard_bam: bool = True,
        variant_callers: str = 'mutect2,muse,lofreq',
        skip_variant_calling: bool = False,
        call_region_bed: str = 'None',
        panel_of_normal_vcf: str = 'None',
        germline_resource_vcf: str = 'None',
        variant_flagging_criteria: str = 'None',
        variant_removal_flags: str = 'None',
        only_pass: bool = False,
        min_snv_callers: int = 1,
        min_indel_callers: int = 1,
        skip_variant_annotation: bool = False,
        vep_db_tar_gz: str = 'None',
        vep_db_type: str = 'merged',
        vep_buffer_size: int = 5000) -> str:

    nas_fastq_dir = nas_fastq_dir.rstrip('/')
    nas_dst_dir = nas_dst_dir.rstrip('/')
    local_fastq_dir = local_fastq_dir.rstrip('/')
    outdir = outdir.rstrip('/')

    # each command needs to pipe stdout and stderr to the progress.txt
    # because when executing a bash script in a screen session, stdout and stderr are not captured outside of the session

    # use single quote to protect every argument

    stdout = f"2>&1 > '{outdir}/progress.txt'"

    rsync_fastq_cmds = [
        f"rsync -avz -e 'ssh -p {nas_port}' {nas_user}@{nas_ip}:'{nas_fastq_dir}/{tumor_fq1}' '{local_fastq_dir}/' {stdout}",
        f"rsync -avz -e 'ssh -p {nas_port}' {nas_user}@{nas_ip}:'{nas_fastq_dir}/{tumor_fq2}' '{local_fastq_dir}/' {stdout}",
    ]

    if normal_fq1 is not None:
        rsync_fastq_cmds += [
            f"rsync -avz -e 'ssh -p {nas_port}' {nas_user}@{nas_ip}:'{nas_fastq_dir}/{normal_fq1}' '{local_fastq_dir}/' {stdout}",
            f"rsync -avz -e 'ssh -p {nas_port}' {nas_user}@{nas_ip}:'{nas_fastq_dir}/{normal_fq2}' '{local_fastq_dir}/' {stdout}",
        ]

    n1 = 'None' if normal_fq1 is None else f'{local_fastq_dir}/{normal_fq1}'
    n2 = 'None' if normal_fq2 is None else f'{local_fastq_dir}/{normal_fq2}'

    somatic_pipeline_cmd = f'''\
python {somatic_pipeline} main \\
--ref-fa='{ref_fa}' \\
--tumor-fq1='{local_fastq_dir}/{tumor_fq1}' \\
--tumor-fq2='{local_fastq_dir}/{tumor_fq2}' \\
--normal-fq1='{n1}' \\
--normal-fq2='{n2}' \\
--outdir='{outdir}' \\
--threads={threads} \\
--umi-length={umi_length} \\
--clip-r1-5-prime={clip_r1_5_prime} \\
--clip-r2-5-prime={clip_r2_5_prime} \\
--read-aligner='{read_aligner}' \\
{'--skip-mark-duplicates' if skip_mark_duplicates else ''} \\
--bqsr-known-variant-vcf='{bqsr_known_variant_vcf}' \\
{'--discard-bam' if discard_bam else ''} \\
--variant-callers='{variant_callers}' \\
{'--skip-variant-calling' if skip_variant_calling else ''} \\
--call-region-bed='{call_region_bed}' \\
--panel-of-normal-vcf='{panel_of_normal_vcf}' \\
--germline-resource-vcf='{germline_resource_vcf}' \\
--variant-flagging-criteria='{variant_flagging_criteria}' \\
--variant-removal-flags='{variant_removal_flags}' \\
{'--only-pass' if only_pass else ''} \\
--min-snv-callers={min_snv_callers} \\
--min-indel-callers={min_indel_callers} \\
{'--skip-variant-annotation' if skip_variant_annotation else ''} \\
--vep-db-tar-gz='{vep_db_tar_gz}' \\
--vep-db-type='{vep_db_type}' \\
--vep-buffer-size={vep_buffer_size} \\
{stdout}'''

    rsync_output_cmd = f"rsync -avz -e 'ssh -p {nas_port}' '{outdir}' {nas_user}@{nas_ip}:'{nas_dst_dir}/'"

    rm_fastq_cmds = [
        f"rm -r '{outdir}'",
        f"rm '{local_fastq_dir}/{tumor_fq1}'",
        f"rm '{local_fastq_dir}/{tumor_fq2}'",
    ]

    if normal_fq1 is not None:
        rm_fastq_cmds += [
            f"rm '{local_fastq_dir}/{normal_fq1}'",
            f"rm '{local_fastq_dir}/{normal_fq2}'",
        ]

    cmds = rsync_fastq_cmds + [somatic_pipeline_cmd] + [rsync_output_cmd] + rm_fastq_cmds

    return '   &&   \\\n'.join(cmds)


def build_submit_cmd(
        job_name: str,
        outdir: str,
        script: str) -> str:

    outdir = outdir.rstrip('/')
    cmd_txt = f'{outdir}/commands.txt'

    # note that when executing a bash script in a screen session, stdout and stderr are not captured outside of the session
    # so the stdout and stderr were written to the progress.txt in the bash script

    cmd = f'''\
mkdir -p "{outdir}"   &&   \\
echo "{script}" > "{cmd_txt}"   &&   \\
screen -S {job_name} -dm bash "{cmd_txt}"
'''

    return cmd
