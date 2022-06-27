import {readFileSync} from "fs";
import {MissingFile} from "../errors/server";

export const readFile = (filePath: string): Buffer => {
    let file: Buffer;
    try {
        file = readFileSync(filePath);
    } catch (err: any) {
        if (err.code === 'ENOENT') {
            throw new MissingFile(filePath);
        } else {
            throw err;
        }
    }
    return file;
};
