import hre from "hardhat";

async function main() {
  const quorumThreshold = 3;

  const DeploymentValidationLedger = await hre.ethers.getContractFactory(
    "DeploymentValidationLedger"
  );

  const contract = await DeploymentValidationLedger.deploy(quorumThreshold);
  await contract.waitForDeployment();

  console.log("DeploymentValidationLedger deployed to:", await contract.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});