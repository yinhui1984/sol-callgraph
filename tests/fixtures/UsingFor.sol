// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

library Lib {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }
}

contract UsingFor {
    using Lib for uint256;
    
    function test(uint256 x) public pure returns (uint256) {
        return x.add(1);
    }
}
