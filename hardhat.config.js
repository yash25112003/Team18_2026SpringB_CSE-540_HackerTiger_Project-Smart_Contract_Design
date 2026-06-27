require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const privateKey = process.env.ETH_PRIVATE_KEY || "";
const hasValidPrivateKey = /^0x[a-fA-F0-9]{64}$/.test(privateKey);

module.exports = {
  solidity: "0.8.20",
  networks: {
    hardhat: {},
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "",
      accounts: hasValidPrivateKey ? [privateKey] : [],
    },
  },
};
