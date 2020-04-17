from common.utils import *
from common import listener_server
import os
import subprocess as sb

output_dir = "covid_lesion_detection_output"
output_path = os.path.join(os.environ["DATA_SHARE_PATH"], output_dir)

def covid_detector(param_dict):

    rel_source_file = param_dict["source_file"][0]
    data_share = os.environ["DATA_SHARE_PATH"]
    source_file = os.path.join(data_share, rel_source_file)

    script_path = "/app/code/keras_retinanet/bin/predict_covid.py"
    model_path = "/app/model/vgg19_csv_01.h5"

    tmp = "/tmp"
    input_path = os.path.join(tmp, "input")

    if not os.path.exists(input_path):
        os.mkdir(input_path)

    cp_cmd = "cp {} {}".format(source_file, input_path)
    log_debug("Running", cp_cmd)
    cp_exit_code = sb.call([cp_cmd], shell=True)
    if cp_exit_code == 1:
        return {}, False


    lesion_detection_cmd = "cd /app/code && python3 {} --model={} --gpu=0 --save-path={} nii {}"\
                            .format(script_path, model_path, output_path, input_path)

    log_debug("Running", lesion_detection_cmd)
    exit_code = sb.call([lesion_detection_cmd], shell=True)
    if exit_code == 1:
        return {}, False

    rm_tmp_input_cmd = "rm -rf {}".format(input_path)
    log_debug("Running", rm_tmp_input_cmd)
    rm_exit_code = sb.call([rm_tmp_input_cmd], shell=True)
    if rm_exit_code == 1:
        return {}, False

    # get names of files
    files = os.listdir(output_path)
    attention_volume = ""
    detection_volume = ""
    for file in files:
        name = os.path.split(file)[1]

        if "attention" in name:
            attention_volume = file
        elif "detection" in name:
            detection_volume = file

    if attention_volume == "" or detection_volume == "":
        return {}, False

    rel_attention_volume_path = os.path.join(output_dir, attention_volume.split()[1])
    rel_detection_volume_path = os.path.join(output_dir, detection_volume.split()[1])

    result_dict = {
        "attention_volume": rel_attention_volume_path,
        "detection_volume": rel_detection_volume_path
    }

    return result_dict, True


if __name__ == "__main__":

    setup_logging()
    log_info("Started listening")

    served_requests = {
        "/covid_detector_nifti": covid_detector
    }

    #make output dir
    
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    listener_server.start_listening(served_requests, multithreaded=True, mark_as_ready_callback=mark_yourself_ready)

