const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const quorumThreshold = 3;
  const [deployer] = await hre.ethers.getSigners();

  const DeploymentValidationLedger = await hre.ethers.getContractFactory(
    "DeploymentValidationLedger"
  );

  const contract = await DeploymentValidationLedger.deploy(quorumThreshold);
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  const network = hre.network.name;
  const explorerUrl =
    network === "sepolia"
      ? `https://sepolia.etherscan.io/address/${address}`
      : null;

  const deploymentRecord = {
    contractName: "DeploymentValidationLedger",
    address,
    deployer: deployer.address,
    network,
    quorumThreshold,
    deployedAt: new Date().toISOString(),
    explorerUrl,
  };

  fs.writeFileSync(
    path.join(__dirname, "..", "deployed-address.json"),
    `${JSON.stringify(deploymentRecord, null, 2)}\n`
  );

  console.log(`Deploying with: ${deployer.address}`);
  console.log(`DeploymentValidationLedger deployed to: ${address}`);
  if (explorerUrl) {
    console.log(`Etherscan: ${explorerUrl}`);
  }
  console.log("Saved deployment metadata to deployed-address.json");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
