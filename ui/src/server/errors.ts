import {Error, ErrorCode} from './types'

export const MissingFile = (filepath: string): Error => {
    return {
        message: `Cannot find ${filepath}.`,
        code: ErrorCode.E_430,
    };
};
