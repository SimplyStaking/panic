const {readdir} = require('fs').promises;
const {resolve} = require('path');
import {MissingFile} from "./errors";
import * as fs from 'fs';

export const readFile = (filePath: string): Buffer => {
    let file: Buffer;
    try {
        file = fs.readFileSync(filePath);
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
    let dirents: fs.Dirent[];
    let foundFiles;
    try {
        dirents = await readdir(dir, {withFileTypes: true});
        foundFiles = await Promise.all(
            dirents.map((dirent: fs.Dirent) => {
                const res: string = resolve(dir, dirent.name);
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
