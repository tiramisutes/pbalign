
import subprocess
import tempfile
import unittest
import os.path
import sys

import pbcommand.testkit
from pbcore.io import AlignmentSet, ConsensusAlignmentSet, openDataSet

import pbtestdata

DATA_DIR = "/pbi/dept/secondary/siv/testdata/SA3-DS"
DATA2 = "/pbi/dept/secondary/siv/testdata/pbalign-unittest2/data"
REF_DIR = "/pbi/dept/secondary/siv/references"


class TestPbalign(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "pbalign "
    REQUIRES_PBCORE = True
    INPUT_FILES = [
        pbtestdata.get_file("subreads-xml"),
        pbtestdata.get_file("lambdaNEB")
    ]
    TASK_OPTIONS = {
        "pbalign.task_options.algorithm_options": "--holeNumbers 1-1000,30000-30500,60000-60600,100000-100500",
    }

    def run_after(self, rtc, output_dir):
        ds_out = openDataSet(rtc.task.output_files[0])
        self.assertTrue(isinstance(ds_out, AlignmentSet),
                        type(ds_out).__name__)


class TestPbalignCCS(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbalign.ccs"
    INPUT_FILES = [
        pbtestdata.get_file("rsii-ccs"),
        pbtestdata.get_file("lambdaNEB")
    ]

    def run_after(self, rtc, output_dir):
        ds_out = openDataSet(rtc.task.output_files[0])
        self.assertTrue(isinstance(ds_out, ConsensusAlignmentSet),
                        type(ds_out).__name__)


class TestPbalignMinorVariants(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbalign.tasks.align_minorvariants"
    INPUT_FILES = [
        pbtestdata.get_file("rsii-ccs"),
        pbtestdata.get_file("lambdaNEB")
    ]

    def run_after(self, rtc, output_dir):
        ds_out = openDataSet(rtc.task.output_files[0])
        self.assertTrue(isinstance(ds_out, ConsensusAlignmentSet),
                        type(ds_out).__name__)


HAVE_BAMTOOLS = False
try:
    with tempfile.TemporaryFile() as O, \
         tempfile.TemporaryFile() as E:
        assert subprocess.call(["bamtools", "--help"], stdout=O, stderr=E) == 0
except Exception as e:
    sys.stderr.write(str(e)+"\n")
    sys.stderr.write("bamtools missing, skipping test\n")
else:
    HAVE_BAMTOOLS = True


@unittest.skipUnless(HAVE_BAMTOOLS, "bamtools not installed")
class TestConsolidateBam(pbcommand.testkit.PbTestApp):
    DRIVER_BASE = "python -m pbalign.tasks.consolidate_alignments"
    INPUT_FILES = [pbtestdata.get_file("aligned-ds-2")]
    TASK_OPTIONS = {
        "pbalign.task_options.consolidate_aligned_bam": True,
    }

    def run_after(self, rtc, output_dir):
        with AlignmentSet(rtc.task.output_files[0]) as f:
            f.assertIndexed()
            self.assertEqual(len(f.toExternalFiles()), 1)
            # test for bug 33778
            qnames = set()
            for rec in f:
                qnames.add(rec.qName)
            self.assertEqual(len(qnames), len(f))


@unittest.skipUnless(HAVE_BAMTOOLS, "bamtools not installed")
class TestConsolidateBamDisabled(TestConsolidateBam):
    TASK_OPTIONS = {
        "pbalign.task_options.consolidate_aligned_bam": False,
    }

    def run_after(self, rtc, output_dir):
        with AlignmentSet(rtc.task.output_files[0]) as f:
            self.assertEqual(len(f.toExternalFiles()), 2)


if __name__ == "__main__":
    unittest.main()
