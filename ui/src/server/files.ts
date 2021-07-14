import {Dirent, promises, readFileSync} from "fs";
import path from 'path';
import {MissingFile} from "./errors";

export const readFile = (filePath: string): Buffer => {
    let file: Buffer;
    try {
        file = readFileSync(filePath);
    } catch (err) {
        if (err.code === 'ENOENT') {
            throw new MissingFile(filePath);
        } else {
            throw err;
        }
    }
    return file;
};

export const getFilesInDir = async (dir: string): Promise<string[]> => {
    let dirents: Dirent[];
    let foundFiles;
    try {
        dirents = await promises.readdir(dir, {withFileTypes: true});
        foundFiles = await Promise.all(
            dirents.map((dirent: Dirent) => {
                const res: string = path.resolve(dir, dirent.name);
                return dirent.isDirectory() ?
                    module.exports.getFiles(res) : res;
            }),
        );
    } catch (err) {
        if (err.code === 'ENOENT') {
            throw new MissingFile(dir);
        } else {
            throw err;
        }
    }
    return Array.prototype.concat(...foundFiles);
};
