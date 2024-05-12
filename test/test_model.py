from setup import TestCase
from src.model import BuildSubmissionCommands, build_execution_script, build_submit_cmd


class TestBuildSubmissionCommands(TestCase):

    def setUp(self):
        self.set_up(py_path=__file__)

    def tearDown(self):
        self.tear_down()

    def test_tn_paired(self):
        actual = BuildSubmissionCommands().main(
            run_table=f'{self.indir}/run_table.csv',
            parameters={
                'NAS User': 'user',
                'NAS Local IP': '255.255.255.255',
                'NAS Port': 22,
            }
        )

    def test_tumor_only(self):
        actual = BuildSubmissionCommands().main(
            run_table=f'{self.indir}/run_table_tumor_only.csv',
            parameters={
                'NAS User': 'user',
                'NAS Local IP': '255.255.255.255',
                'NAS Port': 22,
            }
        )


class TestFunctions(TestCase):

    def test_build_execution_script_tn_paired(self):
        expected = """\
rsync -avz -e 'ssh -p 20' precision@192.168.0.101:'~/NAS_FASTQ/tumor_R1.fastq.gz' './fastq/' 2>&1 > 'outdir/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 20' precision@192.168.0.101:'~/NAS_FASTQ/tumor_R2.fastq.gz' './fastq/' 2>&1 > 'outdir/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 20' precision@192.168.0.101:'~/NAS_FASTQ/normal_R1.fastq.gz' './fastq/' 2>&1 > 'outdir/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 20' precision@192.168.0.101:'~/NAS_FASTQ/normal_R2.fastq.gz' './fastq/' 2>&1 > 'outdir/progress.txt'   &&   \\
python somatic_pipeline-1.0.0 main \\
--ref-fa='./resource/GRCh38.primary_assembly.genome.fa' \\
--tumor-fq1='./fastq/tumor_R1.fastq.gz' \\
--tumor-fq2='./fastq/tumor_R2.fastq.gz' \\
--normal-fq1='./fastq/normal_R1.fastq.gz' \\
--normal-fq2='./fastq/normal_R2.fastq.gz' \\
--outdir='outdir' \\
--threads=4 \\
--umi-length=0 \\
--clip-r1-5-prime=0 \\
--clip-r2-5-prime=0 \\
--read-aligner='bwa' \\
 \\
--bqsr-known-variant-vcf='None' \\
--discard-bam \\
--variant-callers='mutect2,muse,lofreq' \\
 \\
--call-region-bed='None' \\
--panel-of-normal-vcf='None' \\
--germline-resource-vcf='None' \\
--variant-flagging-criteria='None' \\
--variant-removal-flags='None' \\
 \\
--min-snv-callers=1 \\
--min-indel-callers=1 \\
 \\
--vep-db-tar-gz='None' \\
--vep-db-type='merged' \\
--vep-buffer-size=5000 \\
2>&1 > 'outdir/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 20' 'outdir' precision@192.168.0.101:'~/Production/'   &&   \\
rm -r 'outdir'   &&   \\
rm './fastq/tumor_R1.fastq.gz'   &&   \\
rm './fastq/tumor_R2.fastq.gz'   &&   \\
rm './fastq/normal_R1.fastq.gz'   &&   \\
rm './fastq/normal_R2.fastq.gz'"""

        actual = build_execution_script(
            nas_user='precision',
            nas_ip='192.168.0.101',
            nas_port=20,
            nas_fastq_dir='~/NAS_FASTQ/',
            nas_dst_dir='~/Production/',
            tumor_fq1='tumor_R1.fastq.gz',
            tumor_fq2='tumor_R2.fastq.gz',
            normal_fq1='normal_R1.fastq.gz',
            normal_fq2='normal_R2.fastq.gz',
            local_fastq_dir='./fastq/',
            somatic_pipeline='somatic_pipeline-1.0.0',
            ref_fa='./resource/GRCh38.primary_assembly.genome.fa',
            outdir='outdir',
        )
        self.assertEqual(expected, actual)

    def test_build_execution_script_tumor_only(self):
        expected = """\
rsync -avz -e 'ssh -p 20' precision@192.168.0.101:'~/NAS_FASTQ/tumor_R1.fastq.gz' './fastq/' 2>&1 > 'outdir/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 20' precision@192.168.0.101:'~/NAS_FASTQ/tumor_R2.fastq.gz' './fastq/' 2>&1 > 'outdir/progress.txt'   &&   \\
python somatic_pipeline-1.0.0 main \\
--ref-fa='./resource/GRCh38.primary_assembly.genome.fa' \\
--tumor-fq1='./fastq/tumor_R1.fastq.gz' \\
--tumor-fq2='./fastq/tumor_R2.fastq.gz' \\
--normal-fq1='None' \\
--normal-fq2='None' \\
--outdir='outdir' \\
--threads=4 \\
--umi-length=0 \\
--clip-r1-5-prime=0 \\
--clip-r2-5-prime=0 \\
--read-aligner='bwa' \\
--skip-mark-duplicates \\
--bqsr-known-variant-vcf='None' \\
--discard-bam \\
--variant-callers='mutect2,muse,lofreq' \\
--skip-variant-calling \\
--call-region-bed='None' \\
--panel-of-normal-vcf='None' \\
--germline-resource-vcf='None' \\
--variant-flagging-criteria='None' \\
--variant-removal-flags='None' \\
--only-pass \\
--min-snv-callers=1 \\
--min-indel-callers=1 \\
--skip-variant-annotation \\
--vep-db-tar-gz='None' \\
--vep-db-type='merged' \\
--vep-buffer-size=5000 \\
2>&1 > 'outdir/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 20' 'outdir' precision@192.168.0.101:'~/Production/'   &&   \\
rm -r 'outdir'   &&   \\
rm './fastq/tumor_R1.fastq.gz'   &&   \\
rm './fastq/tumor_R2.fastq.gz'"""

        actual = build_execution_script(
            nas_user='precision',
            nas_ip='192.168.0.101',
            nas_port=20,
            nas_fastq_dir='~/NAS_FASTQ/',
            nas_dst_dir='~/Production/',
            tumor_fq1='tumor_R1.fastq.gz',
            tumor_fq2='tumor_R2.fastq.gz',
            normal_fq1=None,
            normal_fq2=None,
            local_fastq_dir='./fastq/',
            somatic_pipeline='somatic_pipeline-1.0.0',
            outdir='outdir',
            ref_fa='./resource/GRCh38.primary_assembly.genome.fa',
            skip_mark_duplicates=True,
            skip_variant_calling=True,
            only_pass=True,
            skip_variant_annotation=True,
        )
        self.assertEqual(expected, actual)

    def test_build_submit_cmd(self):
        expected = '''\
mkdir -p "outdir"   &&   \\
echo "BASH SCRIPT" > "outdir/commands.txt"   &&   \\
screen -S job_name -dm bash "outdir/commands.txt"
'''
        actual = build_submit_cmd(
            job_name='job_name',
            outdir='outdir',
            script='BASH SCRIPT'
        )
        self.assertEqual(expected, actual)
