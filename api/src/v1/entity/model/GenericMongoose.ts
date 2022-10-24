import { Generic } from '../../../../../entities/ts/Generic';

/**
 * Mongoose Generic Model Class
 */
export class GenericMongoose extends Generic {

    public static readonly GIT_HUB = '62a928951f01d1cbcf71f1b7';
    public static readonly DOCKER_HUB = '62a928b868912af15a341ac1';
    
    public constructor() {
        super();
        this.value = String as any;
        this.description = String as any;
        this.group = String as any;
    }
};