from sol_callgraph.selftest_openzeppelin import classify_result

def test_classify_pass():
    # rc_dot=0, rc_list=0, dot_valid='OK', extra_check='PASS' or 'N/A'
    assert classify_result(0, "", 0, "OK", "PASS") == "PASS"
    assert classify_result(0, "", 0, "OK", "N/A") == "PASS"

def test_classify_expected_no_root():
    # rc_dot=3, error contains "no root functions found"
    err = "error: no root functions found in target.sol"
    assert classify_result(3, err, 0, "N/A", "N/A") == "EXPECTED_NO_ROOT"
    
    # Case insensitive check
    assert classify_result(3, "NO ROOT FUNCTIONS FOUND", 0, "N/A", "N/A") == "EXPECTED_NO_ROOT"

def test_classify_fail():
    # rc_dot != 0 and not expected no root
    assert classify_result(1, "some other error", 0, "N/A", "N/A") == "FAIL"
    
    # rc_list != 0
    assert classify_result(0, "", 1, "OK", "N/A") == "FAIL"
    
    # dot_valid != 'OK'
    assert classify_result(0, "", 0, "FAIL", "N/A") == "FAIL"
    
    # extra_check == 'FAIL'
    assert classify_result(0, "", 0, "OK", "FAIL") == "FAIL"
