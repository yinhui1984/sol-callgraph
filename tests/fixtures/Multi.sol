interface I { function i() external; }
library L { function l() public {} }
contract C { function c() public { L.l(); } }
