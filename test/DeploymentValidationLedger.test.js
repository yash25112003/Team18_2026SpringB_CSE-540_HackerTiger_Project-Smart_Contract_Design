const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DeploymentValidationLedger", function () {
  async function deployFixture() {
    const [owner, validator, stranger] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("DeploymentValidationLedger");
    const contract = await Factory.deploy(2);
    await contract.waitForDeployment();
    return { contract, owner, validator, stranger };
  }

  it("initializes with the configured quorum and owner", async function () {
    const { contract, owner } = await deployFixture();

    expect(await contract.owner()).to.equal(owner.address);
    expect(await contract.quorumThreshold()).to.equal(2n);
  });

  it("lets the owner register validators and exposes their profile", async function () {
    const { contract, validator } = await deployFixture();

    await expect(contract.registerValidator(validator.address, "security", 5))
      .to.emit(contract, "ValidatorRegistered")
      .withArgs(validator.address, "security", 5);

    const profile = await contract.getValidator(validator.address);
    expect(profile.isAuthorized).to.equal(true);
    expect(profile.role).to.equal("security");
    expect(profile.weight).to.equal(5n);
    expect(await contract.isValidator(validator.address)).to.equal(true);
  });

  it("prevents unauthorized addresses from voting", async function () {
    const { contract, stranger } = await deployFixture();

    await contract.createSession("repo", "commit123", "artifact123", "ipfs://meta");

    await expect(
      contract.connect(stranger).submitVote(1, true, "evidence://hash")
    ).to.be.revertedWith("Caller is not a validator");
  });

  it("prevents duplicate votes from the same validator", async function () {
    const { contract, owner, validator } = await deployFixture();

    await contract.registerValidator(owner.address, "owner", 10);
    await contract.registerValidator(validator.address, "security", 5);
    await contract.createSession("repo", "commit123", "artifact123", "ipfs://meta");

    await contract.submitVote(1, true, "evidence://owner");
    await expect(
      contract.submitVote(1, false, "evidence://owner-2")
    ).to.be.revertedWith("Validator already voted");

    await contract.connect(validator).submitVote(1, true, "evidence://validator");

    expect(await contract.hasValidatorVoted(1, owner.address)).to.equal(true);
    expect(await contract.hasValidatorVoted(1, validator.address)).to.equal(true);
  });

  it("enforces quorum before finalization and approves majority yes sessions", async function () {
    const { contract, owner, validator } = await deployFixture();

    await contract.registerValidator(owner.address, "owner", 10);
    await contract.registerValidator(validator.address, "security", 5);
    await contract.createSession("repo", "commit123", "artifact123", "ipfs://meta");

    await contract.submitVote(1, true, "evidence://owner");
    await expect(contract.finalizeSession(1)).to.be.revertedWith("Quorum not reached");

    await contract.connect(validator).submitVote(1, true, "evidence://validator");
    await expect(contract.finalizeSession(1))
      .to.emit(contract, "SessionFinalized")
      .withArgs(1, 1);

    const session = await contract.getSession(1);
    expect(session.finalized).to.equal(true);
    expect(session.status).to.equal(1n);
    expect(session.approvals).to.equal(2n);
    expect(session.rejections).to.equal(0n);
  });

  it("rejects sessions when approvals do not exceed rejections", async function () {
    const { contract, owner, validator } = await deployFixture();

    await contract.registerValidator(owner.address, "owner", 10);
    await contract.registerValidator(validator.address, "security", 5);
    await contract.createSession("repo", "commit123", "artifact123", "ipfs://meta");

    await contract.submitVote(1, false, "evidence://owner");
    await contract.connect(validator).submitVote(1, true, "evidence://validator");
    await contract.finalizeSession(1);

    const session = await contract.getSession(1);
    expect(session.status).to.equal(2n);
    expect(session.finalized).to.equal(true);
  });

  it("fails lookup for missing sessions and validators", async function () {
    const { contract, stranger } = await deployFixture();

    await expect(contract.getSession(999)).to.be.revertedWith("Session does not exist");
    await expect(contract.getValidator(stranger.address)).to.be.revertedWith("Validator not found");
  });
});
