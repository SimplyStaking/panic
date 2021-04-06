"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getFilesInDir = exports.readFile = void 0;
const fs_1 = require("fs");
const path_1 = __importDefault(require("path"));
const errors_1 = require("./errors");
const readFile = (filePath) => {
    let file;
    try {
        file = fs_1.readFileSync(filePath);
    }
    catch (err) {
        if (err.code === 'ENOENT') {
            throw new errors_1.MissingFile(filePath);
        }
        else {
            throw err;
        }
    }
    return file;
};
exports.readFile = readFile;
const getFilesInDir = (dir) => __awaiter(void 0, void 0, void 0, function* () {
    let dirents;
    let foundFiles;
    try {
        dirents = yield fs_1.promises.readdir(dir, { withFileTypes: true });
        foundFiles = yield Promise.all(dirents.map((dirent) => {
            const res = path_1.default.resolve(dir, dirent.name);
            return dirent.isDirectory() ?
                module.exports.getFiles(res) : res;
        }));
    }
    catch (err) {
        if (err.code === 'ENOENT') {
            throw new errors_1.MissingFile(dir);
        }
        else {
            throw err;
        }
    }
    return Array.prototype.concat(...foundFiles);
});
exports.getFilesInDir = getFilesInDir;
