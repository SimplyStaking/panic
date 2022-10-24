/**
 * {@link UnknownAlertSeverityError} class represents the error which is thrown
 * when an alert severity value which is not in {@link Severity} is encountered.
 */
import {BaseChains, SourceType} from "./constants";

export class UnknownAlertSeverityError extends Error {
    name = "UnknownAlertSeverityError";

    constructor(severity: string) {
        super(`An unknown alert severity (${severity}) was encountered.`);
    }
}

/**
 * {@link SystemsOverviewNoBaseChainSpecifiedError} class represents the error
 * which is thrown when no base chain is specified within {@link PanicSystemsOverview}.
 */
export class SystemsOverviewNoBaseChainSpecifiedError extends Error {
    name = "SystemsOverviewNoBaseChainSpecifiedError";

    constructor() {
        super(`No base chain was specified within the systems overview component.`);
    }
}

/**
 * {@link SystemsOverviewBaseChainNotFoundError} class represents the error
 * which is thrown when the specified base chain within
 * {@link PanicSystemsOverview} is not found.
 */
export class SystemsOverviewBaseChainNotFoundError extends Error {
    name = "SystemsOverviewBaseChainNotFoundError";

    constructor(baseChainName: string) {
        super(`Base Chain (${baseChainName}) specified within the systems overview component was not found.`);
    }
}

/**
 * {@link UnknownRepoTypeError} class represents the error which is thrown
 * when a repo type value which is not in {@link RepoType} is encountered.
 */
export class UnknownRepoTypeError extends Error {
    name = "UnknownRepoTypeError";

    constructor(repoType: string) {
        super(`An unknown repo type (${repoType}) was encountered.`);
    }
}

/**
 * {@link BaseChainDoesNotSupportSourceTypeError} class represents the error which is thrown
 * when a {@link SourceType} which is not supported by a given base chain is encountered.
 */
export class BaseChainDoesNotSupportSourceTypeError extends Error {
    name = "BaseChainDoesNotSupportSourceTypeError";

    constructor(baseChain: BaseChains, sourceType: SourceType) {
        super(`Base chain (${baseChain}) does not support source type (${sourceType}).`);
    }
}
