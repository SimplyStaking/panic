import {Alert} from "./alerts"
import {RepoType} from "../utils/constants";

/**
 * Represents a base chain.
 */
export interface BaseChain {
    /**
     * Name of base chain.
     */
    readonly name: string;
    /**
     * List of sub-chains in base chain.
     */
    readonly subChains: SubChain[];
}

/**
 * Represents a sub-chain.
 */
export interface SubChain {
    /**
     * Name of sub-chain.
     */
    readonly name: string;
    /**
     * ID of sub-chain.
     */
    readonly id: string;
    /**
     * List of system sources for sub-chain.
     */
    readonly systems: Source[];
    /**
     * List of node sources for sub-chain.
     */
    readonly nodes: Source[];
    /**
     * List of repo sources for sub-chain.
     */
    readonly repos: Repo[];
    /**
     * Whether sub-chain is a source in itself.
     */
    readonly isSource: boolean;
    /**
     * List of alerts for sub-chain.
     */
    alerts: Alert[];
}

/**
 * Represents a source.
 */
export interface Source {
    /**
     * ID of source.
     */
    readonly id: string;
    /**
     * Name of source.
     */
    readonly name: string;
}

/**
 * Represents a repo source.
 */
export interface Repo extends Source {
    /**
     * Type of repo source.
     */
    readonly type: RepoType;
}
