import unittest
from pathlib import Path
from unittest.mock import patch

import sys
import os

# There does not seem to be a cleaner way of doing this in python when working with git submodules
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')))
sys.path.append(os.path.realpath(os.path.join(os.path.realpath(__file__), '../../xtce-generator/src')))

from xtce_generator.src.xtce.xtce_msg_parser import XTCEParser


def test_xtce_msg_parser(monkeypatch, get_data_path):
    monkeypatch.chdir(get_data_path)
    # FIXME:Implement tests for new parser
    ppd = Path('./mdb/ppd.xml').resolve()
    cpd = Path('./mdb/cpd.xml').resolve()
    simlink = Path('./mdb/simlink.xml').resolve()
    ccscds = Path('./mdb/cfs-ccsds.xml').resolve()

    parser = XTCEParser([str(ppd), str(cpd), str(simlink)], str(ccscds), "registry.yaml")

    assert parser._XTCEParser__namespace_dict is not None

    assert parser._XTCEParser__namespace_dict["/cfs/cpd/apps/qae"] is not None

    assert parser._XTCEParser__namespace_dict["/cfs/cpd/apps/qae"][XTCEParser.CONTAINERS_KEY] is not None

    assert parser._XTCEParser__namespace_dict["/cfs/cpd/apps/qae"][XTCEParser.CONTAINERS_KEY][
               "QAE_HK_TLM_MID"] is not None

    assert parser._XTCEParser__namespace_dict["/cfs/cpd/apps/qae"][XTCEParser.CONTAINERS_KEY]["QAE_HK_TLM_MID"][
               XTCEParser.PARAMS_KEY] is not None
    assert parser._XTCEParser__namespace_dict["/cfs/cpd/apps/qae"][XTCEParser.CONTAINERS_KEY]["QAE_HK_TLM_MID"][
               XTCEParser.PARAMS_KEY]["QAE_HK_TLM_MID"][XTCEParser.PARAM_NAME_KEY] == "QAE_HK_TLM_MID"
    assert parser._XTCEParser__namespace_dict["/cfs/cpd/apps/qae"][XTCEParser.CONTAINERS_KEY]["QAE_HK_TLM_MID"][
               XTCEParser.PARAMS_KEY]["QAE_HK_TLM_MID"]["QAE_HK_TLM_MID"]["fields"]["VehicleAttitudeMsg"]["fields"][
               "Q"] is not None
    q_field = parser._XTCEParser__namespace_dict["/cfs/cpd/apps/qae"][XTCEParser.CONTAINERS_KEY]["QAE_HK_TLM_MID"][
        XTCEParser.PARAMS_KEY]["QAE_HK_TLM_MID"]["QAE_HK_TLM_MID"]["fields"]["VehicleAttitudeMsg"]["fields"]["Q"]
    # FIXME:Fix importing here
    # assert isinstance(q_field[XTCEParser.ARRAY_TYPE_KEY][0], xtce.FloatParameterType)

    tlm_map = parser.get_msg_ids_at('/cfs/cpd/core/cfe/cfe_es')

    assert tlm_map is not None
    assert tlm_map['CFE_ES_HK_TLM_MID']['msgID'] == 2575

    command = parser.craft_command("/cfs/cpd/core/cfe/cfe_es/Noop", {})

    assert command is not None

    tlm_command = parser.craft_tlm_command("/cfs/cpd/apps/qae/QAE_HK_TLM_MID", {})

    assert tlm_command is not None


if __name__ == '__main__':
    unittest.main()
