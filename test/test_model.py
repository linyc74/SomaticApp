import pandas as pd
from src.model import BuildSubmissionCommands, BuildExecutionScript, build_submit_cmd, is_subdir
from .setup import TestCase


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
            'NAS User': 'me',
            'NAS Destination Directory': 'test',
            'umi-length': '7',
            'skip-mark-duplicates': True,
            'bqsr-known-variant-vcf': 'BQSR_KNOWN_VARIANT_VCF',
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

        actual = BuildExecutionScript().main(parameters=parameters, sample_row=sample_row)

        expected = """\
rsync -avz -e 'ssh -p 22' me@255.255.255.255:'/SEQUENCING_BATCH_ID/TUMOR_R1.fastq.gz' './fastq/' 2>&1 >> 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' me@255.255.255.255:'/SEQUENCING_BATCH_ID/TUMOR_R2.fastq.gz' './fastq/' 2>&1 >> 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' me@255.255.255.255:'/SEQUENCING_BATCH_ID/NORMAL_R1.fastq.gz' './fastq/' 2>&1 >> 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' me@255.255.255.255:'/SEQUENCING_BATCH_ID/NORMAL_R2.fastq.gz' './fastq/' 2>&1 >> 'OUTPUT_NAME/progress.txt'   &&   \\
python somatic_pipeline-1.0.0 main \\
--tumor-fq1='./fastq/TUMOR_R1.fastq.gz' \\
--tumor-fq2='./fastq/TUMOR_R2.fastq.gz' \\
--call-region-bed='resource/bed/BED_FILE.bed' \\
--outdir='OUTPUT_NAME' \\
--normal-fq1='./fastq/NORMAL_R1.fastq.gz' \\
--normal-fq2='./fastq/NORMAL_R2.fastq.gz' \\
--ref-fa='resource/GRCh38.primary_assembly.genome.fa' \\
--threads=4 \\
--umi-length=7 \\
--clip-r1-5-prime=0 \\
--clip-r2-5-prime=0 \\
--read-aligner='bwa' \\
--skip-mark-duplicates \\
--bqsr-known-variant-vcf='BQSR_KNOWN_VARIANT_VCF' \\
--variant-callers='mutect2,muse,lofreq' \\
--panel-of-normal-vcf='None' \\
--germline-resource-vcf='None' \\
--variant-flagging-criteria='None' \\
--variant-removal-flags='None' \\
--min-snv-callers=1 \\
--min-indel-callers=1 \\
--vep-db-tar-gz='None' \\
--vep-db-type='merged' \\
--vep-buffer-size=5000 \\
2>&1 >> 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' 'OUTPUT_NAME' me@255.255.255.255:'~/SomaticApp/test/'   &&   \\
rm -r 'OUTPUT_NAME'   &&   \\
rm './fastq/TUMOR_R1.fastq.gz'   &&   \\
rm './fastq/TUMOR_R2.fastq.gz'   &&   \\
rm './fastq/NORMAL_R1.fastq.gz'   &&   \\
rm './fastq/NORMAL_R2.fastq.gz'"""
        self.assertEqual(expected, actual)

    def test_tumor_only(self):
        parameters = {
            'NAS User': 'me',
            'umi-length': 7,
            'skip-mark-duplicates': True,
            'bqsr-known-variant-vcf': 'BQSR_KNOWN_VARIANT_VCF',
        }
        sample_row = pd.Series({
            'Sequencing Batch ID': 'SEQUENCING_BATCH_ID',
            'Tumor Fastq R1': 'TUMOR_R1.fastq.gz',
            'Tumor Fastq R2': 'TUMOR_R2.fastq.gz',
            'Normal Fastq R1': pd.NA,
            'Normal Fastq R2': pd.NA,
            'Output Name': 'OUTPUT_NAME',
            'BED File': 'BED_FILE.bed',
        })
        actual = BuildExecutionScript().main(parameters=parameters, sample_row=sample_row)

        expected = """\
rsync -avz -e 'ssh -p 22' me@255.255.255.255:'/SEQUENCING_BATCH_ID/TUMOR_R1.fastq.gz' './fastq/' 2>&1 >> 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' me@255.255.255.255:'/SEQUENCING_BATCH_ID/TUMOR_R2.fastq.gz' './fastq/' 2>&1 >> 'OUTPUT_NAME/progress.txt'   &&   \\
python somatic_pipeline-1.0.0 main \\
--tumor-fq1='./fastq/TUMOR_R1.fastq.gz' \\
--tumor-fq2='./fastq/TUMOR_R2.fastq.gz' \\
--call-region-bed='resource/bed/BED_FILE.bed' \\
--outdir='OUTPUT_NAME' \\
--ref-fa='resource/GRCh38.primary_assembly.genome.fa' \\
--threads=4 \\
--umi-length=7 \\
--clip-r1-5-prime=0 \\
--clip-r2-5-prime=0 \\
--read-aligner='bwa' \\
--skip-mark-duplicates \\
--bqsr-known-variant-vcf='BQSR_KNOWN_VARIANT_VCF' \\
--variant-callers='mutect2,muse,lofreq' \\
--panel-of-normal-vcf='None' \\
--germline-resource-vcf='None' \\
--variant-flagging-criteria='None' \\
--variant-removal-flags='None' \\
--min-snv-callers=1 \\
--min-indel-callers=1 \\
--vep-db-tar-gz='None' \\
--vep-db-type='merged' \\
--vep-buffer-size=5000 \\
2>&1 >> 'OUTPUT_NAME/progress.txt'   &&   \\
rsync -avz -e 'ssh -p 22' 'OUTPUT_NAME' me@255.255.255.255:'~/SomaticApp/'   &&   \\
rm -r 'OUTPUT_NAME'   &&   \\
rm './fastq/TUMOR_R1.fastq.gz'   &&   \\
rm './fastq/TUMOR_R2.fastq.gz'"""
        self.assertEqual(expected, actual)

    def test_raise_dstdir_error(self):
        # multiple '../' buried in the path is dangerous, causing writing to super directories or even root
        parameters = {
            'NAS Destination Directory': 'A/B/../.././../../',
        }
        sample_row = pd.Series({
            'Sequencing Batch ID': 'SEQUENCING_BATCH_ID',
            'Tumor Fastq R1': 'TUMOR_R1.fastq.gz',
            'Tumor Fastq R2': 'TUMOR_R2.fastq.gz',
            'Normal Fastq R1': pd.NA,
            'Normal Fastq R2': pd.NA,
            'Output Name': 'OUTPUT_NAME',
            'BED File': 'BED_FILE.bed',
        })
        with self.assertRaises(ValueError):
            BuildExecutionScript().main(parameters=parameters, sample_row=sample_row)


class TestFunctions(TestCase):

    def test_is_subdir(self):
        self.assertTrue(is_subdir(parent='~/A', child='~/A'))  # same directory is considered subdir
        self.assertTrue(is_subdir(parent='~/A', child='~/A/B'))
        self.assertTrue(is_subdir(parent='~/A', child='~/A/../A'))  # same directory is considered subdir
        self.assertFalse(is_subdir(parent='~/A', child='~/A/../'))
        self.assertFalse(is_subdir(parent='~/A', child='~/A/../B'))

    def test_build_submit_cmd(self):
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
