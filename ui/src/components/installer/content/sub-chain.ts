export const MAIN_TEXT = `PANIC works with the concept of "base chains" and "sub-chains".`;
export const BULLET_ONE = `Supported base chains: Cosmos-SDK, Substrate, Chainlink or General - Used to represent any systems or repositories not associated with a blockchain. For example, the host machine that PANIC is running on.`;
export const BULLET_TWO = `Sub-chains are any protocol built on top of the base chains. For example, Akash (Cosmos-SDK), Polkadot (Substrate).`;
export const MORE_INFO_MESSAGES = [
    {
        title: "Introduction",
        messages: [
            "A running blockchain software you want alerts for and have monitored by PANIC.",
            "Your chosen base chain will be the underlying technology building the blockchain."
        ]
    },
    {
        title: "How are they set up?",
        messages: [
        `
            Step 1: Choose the base chain. For example, Cosmos-SDK.
        `,
        `
            Step 2: Name the sub-chain. For example, Akash.
        `,
        `
            Step 3: Once your sub-chain is ready (steps 1 and 2), you will be adding channels, nodes, repositories, and altering configuration for this sub-chain using this installer.
        `
        ]
    },
    {
        title: "Supported Frameworks (base chains)",
        messages: [
        `
            Cosmos-SDK: Framework released by the Interchain Foundation for building application-specific blockchains.
        `,
        `
            Substrate: Framework released by the Web3 Foundation for building application-specific blockchains.
        `,
        `
            Chainlink: Decentralized oracle networks provide tamper-proof inputs, outputs, and computations to support advanced smart contracts on any blockchain.
        `,
        `
            General: Here you can monitor host systems and repositories which do not belong to any blockchain.
        `,
        ]
    }
];