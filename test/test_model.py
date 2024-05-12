import pandas as pd
from setup import TestCase
from src.model import BuildSubmissionCommands, BuildExecutionScript, build_submit_cmd


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


class TestBuildExecutionScript(TestCase):

    def test_tn_paired(self):
        parameters = {

        }
        sample_row = pd.Series({
            'Sequencing Batch ID': 'SEQUENCING_BATCH_ID',
            'Tumor Fastq R1': 'TUMOR_R1.fastq.gz',
            'Tumor Fastq R2': 'TUMOR_R2.fastq.gz',
            'Normal Fastq R1': 'NORMAL_R1.fastq.gz',
            'Normal Fastq R2': 'NORMAL_R2.fastq.gz',
            'Output Name': 'OUTPUT_NAME',
            'BED File': 'BED_FILE.bed',
        })
        actual = BuildExecutionScript().main(
            parameters=parameters,
            sample_row=sample_row)
        expected = """\
rsync -avz -e 'ssh -p 22' @255.255.255.255:'/SEQUENCING_BATCH_ID/TUMOR_R1.fastq.gz' './fastq/' 2>&1 > 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' @255.255.255.255:'/SEQUENCING_BATCH_ID/TUMOR_R2.fastq.gz' './fastq/' 2>&1 > 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' @255.255.255.255:'/SEQUENCING_BATCH_ID/NORMAL_R1.fastq.gz' './fastq/' 2>&1 > 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' @255.255.255.255:'/SEQUENCING_BATCH_ID/NORMAL_R2.fastq.gz' './fastq/' 2>&1 > 'OUTPUT_NAME/progress.txt'   &&   \\
python somatic_pipeline-1.0.0 main \\
--ref-fa='resource/GRCh38.primary_assembly.genome.fa' \\
--tumor-fq1='./fastq/TUMOR_R1.fastq.gz' \\
--tumor-fq2='./fastq/TUMOR_R2.fastq.gz' \\
--normal-fq1='./fastq/NORMAL_R1.fastq.gz' \\
--normal-fq2='./fastq/NORMAL_R2.fastq.gz' \\
--outdir='OUTPUT_NAME' \\
--threads=4 \\
--umi-length=0 \\
--clip-r1-5-prime=0 \\
--clip-r2-5-prime=0 \\
--read-aligner='bwa' \\
 \\
--bqsr-known-variant-vcf='None' \\
 \\
--variant-callers='mutect2,muse,lofreq' \\
 \\
--call-region-bed='resource/bed/BED_FILE.bed' \\
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
2>&1 > 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' 'OUTPUT_NAME' @255.255.255.255:'/'   &&   \\
rm -r 'OUTPUT_NAME'   &&   \\
rm './fastq/TUMOR_R1.fastq.gz'   &&   \\
rm './fastq/TUMOR_R2.fastq.gz'   &&   \\
rm './fastq/NORMAL_R1.fastq.gz'   &&   \\
rm './fastq/NORMAL_R2.fastq.gz'"""
        self.assertEqual(expected, actual)

    def test_tumor_only(self):
        parameters = {

        }
        sample_row = pd.Series({
            'Sequencing Batch ID': 'SEQUENCING_BATCH_ID',
            'Tumor Fastq R1': 'TUMOR_R1.fastq.gz',
            'Tumor Fastq R2': 'TUMOR_R2.fastq.gz',
            'Output Name': 'OUTPUT_NAME',
            'BED File': 'BED_FILE.bed',
        })
        actual = BuildExecutionScript().main(
            parameters=parameters,
            sample_row=sample_row
        )
        expected = """\
rsync -avz -e 'ssh -p 22' @255.255.255.255:'/SEQUENCING_BATCH_ID/TUMOR_R1.fastq.gz' './fastq/' 2>&1 > 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' @255.255.255.255:'/SEQUENCING_BATCH_ID/TUMOR_R2.fastq.gz' './fastq/' 2>&1 > 'OUTPUT_NAME/progress.txt'   &&   \\
python somatic_pipeline-1.0.0 main \\
--ref-fa='resource/GRCh38.primary_assembly.genome.fa' \\
--tumor-fq1='./fastq/TUMOR_R1.fastq.gz' \\
--tumor-fq2='./fastq/TUMOR_R2.fastq.gz' \\
--normal-fq1='None' \\
--normal-fq2='None' \\
--outdir='OUTPUT_NAME' \\
--threads=4 \\
--umi-length=0 \\
--clip-r1-5-prime=0 \\
--clip-r2-5-prime=0 \\
--read-aligner='bwa' \\
 \\
--bqsr-known-variant-vcf='None' \\
 \\
--variant-callers='mutect2,muse,lofreq' \\
 \\
--call-region-bed='resource/bed/BED_FILE.bed' \\
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
2>&1 > 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' 'OUTPUT_NAME' @255.255.255.255:'/'   &&   \\
rm -r 'OUTPUT_NAME'   &&   \\
rm './fastq/TUMOR_R1.fastq.gz'   &&   \\
rm './fastq/TUMOR_R2.fastq.gz'"""
        self.assertEqual(expected, actual)


class TestBuildSubmitCmd(TestCase):

    def test_main(self):
        actual = build_submit_cmd(
            job_name='job_name',
            outdir='outdir',
            script='BASH SCRIPT'
        )
        expected = '''\
mkdir -p "outdir"   &&   \\
echo "BASH SCRIPT" > "outdir/commands.txt"   &&   \\
screen -S job_name -dm bash "outdir/commands.txt"
'''
        self.assertEqual(expected, actual)
