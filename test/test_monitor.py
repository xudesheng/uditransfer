import unittest
import sys
import os
import shutil
import logging
import stat
import codecs

try:
    from uditransfer import monitor
    from uditransfer import configuration
    from uditransfer import util
except:
    sys.path.append("..")
    from uditransfer import monitor
    from uditransfer import configuration
    from uditransfer import util

class MonitorTestCase(unittest.TestCase):

    def setUp(self):
        self.flag = True

        self.folder_sample = "../sample"
        self.folder_hl7 = "../sample/HL7"
        self.folder_acks = "../sample/ACKs"
        self.folder_ghxack = "../sample/ack"
        self.config = configuration.monitor_configuration("../sample/sample_config.ini")
        self.cleanse_files()

    def test_sample_data(self):
        assert(os.path.exists(self.folder_sample))
        assert(os.path.exists(self.folder_hl7))
        assert(os.path.exists(self.folder_acks))
        assert(os.path.exists(self.folder_ghxack))
        assert(len(list(os.listdir(self.folder_hl7)))>0)
        assert (len(list(os.listdir(self.folder_acks))) > 0)
        assert(len(list(os.listdir(self.folder_ghxack)))>0)
        assert(os.path.exists(self.config.folder_localinbox))

    def test_ack3_encoding(self):
        ack3_file_name = r'ci1474006022846.2416915@fdsuv05638_te1.xml'
        ghx_ack_file = os.path.join(self.folder_ghxack,"temp", ack3_file_name)
        assert(os.path.exists(ghx_ack_file))

        ghx_asc_content = None
        ghx_utf_content = None

        with open(ghx_ack_file, 'r') as content_file:
            ghx_asc_content = content_file.read()

        with codecs.open(ghx_ack_file, 'r', encoding="utf8") as content_file:
            ghx_utf_content = content_file.read()

        print("ASC_Content:\n%s" % (ghx_asc_content))
        print("\n\nUTF Content:\n%s" % (ghx_utf_content))

        coreID_asc = monitor.get_coreid_from_ack3_content(ghx_asc_content)
        coreID_utf = monitor.get_coreid_from_ack3_content(ghx_utf_content)
        print("ASC CoreID:%s" % coreID_asc)
        print("\n\nUTF CoreID:%s" % coreID_utf)
        assert(coreID_asc == coreID_utf)

    def test_detect_ack_file(self):
        ack1_file = r'../sample/ACKs/fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack2_file = r'../sample/ACKs/ACK2_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack3_file = r'../sample/ACKs/ACK3_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        row_message_id = r'fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        row_core_id = r'fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gzCOREID'

        assert(os.path.exists(ack1_file))
        ack1_content = self.read_file_content(ack1_file)
        message_id = monitor.get_messageid_from_ack1_content(ack1_content)
        assert(row_message_id == message_id)

        core_id = monitor.get_coreid_from_ack2_content(ack1_content)
        assert(not core_id)

        assert(os.path.exists(ack2_file))
        ack2_content = self.read_file_content(ack2_file)
        message_id = monitor.get_messageid_from_ack2_content(ack2_content)
        assert(message_id == row_message_id)

        core_id = monitor.get_coreid_from_ack2_content(ack2_content)
        assert(core_id == row_core_id)

        assert(os.path.exists(ack3_file))
        ack3_content = self.read_file_content(ack3_file)
        core_id = monitor.get_coreid_from_ack3_content(ack3_content)
        assert(core_id == row_core_id)

        core_id = monitor.get_coreid_from_ack3_content(ack1_content)
        assert(not core_id)

        core_id = monitor.get_coreid_from_ack3_content(ack2_content)
        assert(not core_id)

    def test_is_valid_hl7_message(self):
        hl7_1_file = r'../sample/HL7/fda_15ff7927-91f6-4fd8-80cb-bbddc6fa0cd1.tar.gz'
        hl7_2_file = r'../sample/HL7/fda_a383c97e-5749-4c0c-aff9-1f3883a34191.tar.gz'
        hl7_3_file = r'../sample/HL7/fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack1_file = r'../sample/ACKs/fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack2_file = r'../sample/ACKs/ACK2_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack3_file = r'../sample/ACKs/ACK3_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        assert (monitor.is_valid_hl7_message(hl7_1_file))
        assert (monitor.is_valid_hl7_message(hl7_2_file))
        assert (monitor.is_valid_hl7_message(hl7_3_file))

        assert (not monitor.is_valid_hl7_message(ack1_file))
        assert (not monitor.is_valid_hl7_message(ack2_file))
        assert (not monitor.is_valid_hl7_message(ack3_file))


    def test_process_orphan_acks(self):
        ack1_file = r'fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack2_file = r'ACK2_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        ack3_file = r'ACK3_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'

        assert(os.path.exists(self.config.folder_remoteorphan))

        ack_files = monitor.get_file_list(self.folder_acks)
        #ack_files = [ack1_file, ack2_file, ack3_file]
        for ack in ack_files:
            src_file = os.path.join(self.folder_acks, ack)
            target_file = os.path.join(self.config.folder_remoteorphan, ack)
            shutil.copyfile(src_file, target_file)
        #print(os.listdir(self.config.folder_remoteorphan))
        assert(len(ack_files) == len(list(os.listdir(self.config.folder_remoteorphan))))
        assert(os.path.exists(os.path.join(self.config.folder_remoteorphan, ack1_file)))
        assert (os.path.exists(os.path.join(self.config.folder_remoteorphan, ack2_file)))
        assert (os.path.exists(os.path.join(self.config.folder_remoteorphan, ack3_file)))

        hl7_files = monitor.get_file_list(self.folder_hl7)
        for hl7 in hl7_files:
            if hl7 in ack_files:
                src_file = os.path.join(self.folder_hl7, hl7)
                target_file = os.path.join(self.config.folder_ack1flag, hl7)
                shutil.copyfile(src_file, target_file)
                monitor.process_ack_shell_commands(self.config, target_file)
                assert (oct(os.stat(target_file)[stat.ST_MODE])[-3:] == '666')

        orphan_files = monitor.get_file_list(self.config.folder_remoteorphan)
        #assert(len(orphan_files) == len(ack_files))

        monitor.process_orphan_acks(self.config)
        local_inbox_files = monitor.get_file_list(self.config.folder_localinbox)
        assert (len(local_inbox_files) == 1)

        monitor.process_orphan_acks(self.config)
        local_inbox_files = monitor.get_file_list(self.config.folder_localinbox)
        assert (len(local_inbox_files) == 2)

        monitor.process_orphan_acks(self.config)

        local_inbox_files = monitor.get_file_list(self.config.folder_localinbox)
        assert(len(local_inbox_files) == 3)
        assert (os.path.exists(os.path.join(self.config.folder_localinbox, ack1_file)))
        assert (os.path.exists(os.path.join(self.config.folder_localinbox, ack2_file)))
        assert (os.path.exists(os.path.join(self.config.folder_localinbox, ack3_file)))

        #assert(not os.path.exists(ack1_flag))

    def test_chmod_command(self):
        assert (self.config)
        assert (self.config.folder_remoteoutbox)
        hl7_1_file = r'../sample/HL7/fda_15ff7927-91f6-4fd8-80cb-bbddc6fa0cd1.tar.gz'
        hl7_2_file = r'../sample/HL7/fda_a383c97e-5749-4c0c-aff9-1f3883a34191.tar.gz'
        hl7_3_file = r'../sample/HL7/fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'

        onlyfiles = [hl7_1_file, hl7_2_file, hl7_3_file]

        for hl7_file in onlyfiles:
            srcfile = os.path.join(self.folder_hl7, os.path.basename(hl7_file))
            tgtfile = os.path.join(self.config.folder_localoutbox, os.path.basename(hl7_file))
            shutil.copyfile(srcfile, tgtfile)
            assert(os.path.exists(tgtfile))
            monitor.process_hl7_shell_commands(self.config, tgtfile)
            assert (oct(os.stat(tgtfile)[stat.ST_MODE])[-3:] == '666')

        total_files = len(onlyfiles)
        files_in_localoutbox = monitor.get_file_list(self.config.folder_localoutbox)
        assert (len(files_in_localoutbox) == total_files)

        monitor.process_hl7_message(self.config)

        files_in_localoutbox = monitor.get_file_list(self.config.folder_localoutbox)
        assert(len(files_in_localoutbox)==0)

        files_in_ac1flag = monitor.get_file_list(self.config.folder_ack1flag)
        assert(len(files_in_ac1flag) == total_files)

        files_in_remoteoutbox = monitor.get_file_list(self.config.folder_remoteoutbox)
        assert(len(files_in_remoteoutbox) == total_files)


    def test_process_wrong_hl7_message(self):
        assert (self.config)
        assert (self.config.folder_localinbox)
        hl7_1_file_wrong = r'../sample/ACKs/fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        hl7_2_file_wrong = r'../sample/ACKs/ACK2_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'
        hl7_3_file_wrong = r'../sample/ACKs/ACK3_fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'

        onlyfiles = [hl7_1_file_wrong, hl7_2_file_wrong, hl7_3_file_wrong]
        for hl7_file in onlyfiles:
            srcfile = os.path.join(self.folder_acks, os.path.basename(hl7_file))
            tgtfile = os.path.join(self.config.folder_localoutbox, os.path.basename(hl7_file))
            shutil.copyfile(srcfile, tgtfile)
            assert (os.path.exists(tgtfile))

        total_files = len(onlyfiles)
        files_in_localoutbox = monitor.get_file_list(self.config.folder_localoutbox)
        assert (len(files_in_localoutbox) == total_files)

        monitor.process_hl7_message(self.config)

        files_in_localoutbox = monitor.get_file_list(self.config.folder_localoutbox)
        assert (len(files_in_localoutbox) == 0)

        files_in_ac1flag = monitor.get_file_list(self.config.folder_ack1flag)
        assert (len(files_in_ac1flag) == 0)

        files_in_remoteoutbox = monitor.get_file_list(self.config.folder_remoteoutbox)
        assert (len(files_in_remoteoutbox) == 0)

        files_in_hl7flag = monitor.get_file_list(self.config.folder_hl7flag)
        assert (len(files_in_hl7flag) == total_files)

    def test_process_hl7_message(self):
        assert(self.config)
        assert(self.config.folder_localoutbox)
        hl7_1_file = r'../sample/HL7/fda_15ff7927-91f6-4fd8-80cb-bbddc6fa0cd1.tar.gz'
        hl7_2_file = r'../sample/HL7/fda_a383c97e-5749-4c0c-aff9-1f3883a34191.tar.gz'
        hl7_3_file = r'../sample/HL7/fda_f012caf2-d546-4885-a2e6-0640dfd408e2.tar.gz'

        onlyfiles = [hl7_1_file, hl7_2_file, hl7_3_file]

        for hl7_file in onlyfiles:
            srcfile = os.path.join(self.folder_hl7, os.path.basename(hl7_file))
            tgtfile = os.path.join(self.config.folder_localoutbox, os.path.basename(hl7_file))
            shutil.copyfile(srcfile, tgtfile)
            assert(os.path.exists(tgtfile))

        total_files = len(onlyfiles)
        files_in_localoutbox = monitor.get_file_list(self.config.folder_localoutbox)
        assert (len(files_in_localoutbox) == total_files)

        monitor.process_hl7_message(self.config)

        for hl7_file in onlyfiles:
            tgtfile = os.path.join(self.config.folder_remoteoutbox, os.path.basename(hl7_file))
            assert (os.path.exists(tgtfile))
            assert (oct(os.stat(tgtfile)[stat.ST_MODE])[-3:] == '666')

        files_in_localoutbox = monitor.get_file_list(self.config.folder_localoutbox)
        assert(len(files_in_localoutbox)==0)

        files_in_ac1flag = monitor.get_file_list(self.config.folder_ack1flag)
        assert(len(files_in_ac1flag) == total_files)

        files_in_remoteoutbox = monitor.get_file_list(self.config.folder_remoteoutbox)
        assert(len(files_in_remoteoutbox) == total_files)

    def read_file_content(self, file_name):
        with open(file_name, 'r') as content_file:
            return content_file.read()

    def cleanse_files(self):

        folder_list = [self.config.folder_localinbox, self.config.folder_localoutbox,
                       self.config.folder_remoteinbox, self.config.folder_remoteoutbox,
                       self.config.folder_remoteorphan, self.config.folder_ack1flag,
                       self.config.folder_ack2flag, self.config.folder_ack3flag,
                       self.config.folder_tobedeleted]

        for one_folder in folder_list:
            onlyfiles = monitor.get_file_list(one_folder)
            for one_file in onlyfiles:
                file_tobedelete = os.path.join(one_folder, one_file)
                os.remove(file_tobedelete)

if __name__=="__main__":
    util.initialize_logger("../temp/logs/")
    unittest.main()

