// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Base {
    function baseFunc() public virtual {}
}

contract Derived is Base {
    modifier onlyAdmin() {
        checkAdmin();
        _;
    }

    function checkAdmin() internal {
        // some check
    }

    function declaredFunc() public onlyAdmin {
        baseFunc();
    }
    
    // baseFunc is inherited, not declared here
}
