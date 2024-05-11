from src.io import IO
from .setup import TestCase


class TestIO(TestCase):

    def setUp(self):
        self.set_up(py_path=__file__)

    def tearDown(self):
        self.tear_down()

    def test_read_txt(self):
        actual = IO().read(f'{self.indir}/parameters.txt')
        self.assertEqual(actual['User'], 'me')
        self.assertEqual(actual['skip-otu'], True)
        self.assertEqual(actual['colors'], "'#59A257,#4A759D'")

    def test_read_tsv(self):
        actual = IO().read(f'{self.indir}/parameters.tsv')
        self.assertEqual(actual['User'], 'me')
        self.assertEqual(actual['skip-otu'], True)
        self.assertEqual(actual['colors'], "'#59A257,#4A759D'")

    def test_read_csv(self):
        actual = IO().read(f'{self.indir}/parameters.csv')
        self.assertEqual(actual['User'], 'me')
        self.assertEqual(actual['skip-otu'], True)
        self.assertEqual(actual['colors'], "'#59A257,#4A759D'")

    def test_write_txt(self):
        IO().write(
            parameters={
                'User': 'me',
                'Host': '255.255.255.255',
                'skip-otu': True,
                'flag': False,  # should not be written
                'colors': "'#59A257,#4A759D'",
            },
            file=f'{self.outdir}/written.txt'
        )
        self.assertFileEqual(
            f'{self.outdir}/written.txt',
            f'{self.indir}/written.txt'
        )

    def test_write_csv(self):
        IO().write(
            parameters={
                'User': 'me',
                'Host': '255.255.255.255',
                'skip-otu': True,
                'flag': False,  # should not be written
                'colors': "'#59A257,#4A759D'",
            },
            file=f'{self.outdir}/written.csv'
        )
        self.assertFileEqual(
            f'{self.outdir}/written.csv',
            f'{self.indir}/written.csv'
        )
