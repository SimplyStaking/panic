import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';
import { SlackOldModelBuilder } 
    from '../../../builder/channels/SlackOldModelBuilder';

const builder = new SlackOldModelBuilder();
new ModelBuildDirector(builder);

export const SlackOldModel = builder.model;
