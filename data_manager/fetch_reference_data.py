#!/usr/bin/env python
# ref: https://galaxyproject.org/admin/tools/data-managers/how-to/define/

import sys
import os
import tempfile
import shutil
import argparse
import urllib2
import tarfile

from galaxy.util.json import from_json_string, to_json_string


def cleanup_before_exit(tmp_dir):
    if tmp_dir and os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

def stop_err(msg):
    sys.stderr.write(msg)
    sys.exit(1)

def get_reference_id_name(params):
    genome_id = params['param_dict']['genome_id']
    genome_name = params['param_dict']['genome_name']
    return genome_id, genome_name

def get_url(params):
    trained_url = params['param_dict']['trained_url']
    return trained_url

def download_from_GlimmerHMM(data_manager_dict, target_directory, sequence_id, sequence_name, trained_dir):
    if not trained_dir:
        trained_dir = 'ftp://ccb.jhu.edu/pub/software/glimmerhmm/GlimmerHMM-3.0.4.tar.gz'
    #Download trained data, ref: https://dzone.com/articles/how-download-file-python
    f = urllib2.urlopen(trained_dir)
    data = f.read()
    downloadpath = 'tmp'
    os.mkdir(downloadpath)
    filepath = os.path.join(downloadpath, 'GlimmerHMM-3.0.4.tar')
    with open(filepath, 'wb') as code:
        code.write(data)
    with tarfile.open(filepath, mode='r:*') as tar:
        subdir = [
          tarinfo for tarinfo in tar.getmembers()
          if sequence_id in tarinfo.name
        ]
        tar.extractall(path=downloadpath, members=subdir)
    glimmerhmm_trained_dir = os.path.join(downloadpath, 'GlimmerHMM', 'trained_dir', sequence_id)
    glimmerhmm_trained_target_dir = os.path.join(target_directory, sequence_id)
    shutil.copytree(glimmerhmm_trained_dir, glimmerhmm_trained_target_dir)
    data_table_entry = dict(value=sequence_id, name=sequence_name, path=glimmerhmm_trained_target_dir)
    _add_data_table_entry(data_manager_dict, data_table_entry)
    
    cleanup_before_exit('tmp')

def _add_data_table_entry(data_manager_dict, data_table_entry):
    data_manager_dict['data_tables'] = data_manager_dict.get('data_tables', {})
    data_manager_dict['data_tables']['glimmer_hmm_trained_dir'] = data_manager_dict['data_tables'].get('glimmer_hmm_trained_dir', [])
    data_manager_dict['data_tables']['glimmer_hmm_trained_dir'].append(data_table_entry)
    return data_manager_dict

def main():
    #Parse Command Line
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--out', help='Output file')
    args = parser.parse_args()

    filename = args.out

    params = from_json_string(open(filename).read())
    target_directory = params['output_data'][0]['extra_files_path']
    os.mkdir(target_directory)
    data_manager_dict = {}

    sequence_id, sequence_name = get_reference_id_name(params)
    trained_dir = get_url(params)
    #Fetch the FASTA
    download_from_GlimmerHMM(data_manager_dict, target_directory, sequence_id, sequence_name, trained_dir)
    #save info to json file
    open(filename, 'wb').write(to_json_string(data_manager_dict))

if __name__ == "__main__":
    main()

