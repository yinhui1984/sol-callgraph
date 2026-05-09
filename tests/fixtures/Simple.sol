// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Simple {
    function foo() public {
        bar();
    }

    function bar() public {
        // internal call
    }
}
