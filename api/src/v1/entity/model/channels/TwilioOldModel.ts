import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';
import { TwillioOldModelBuilder } 
    from '../../../builder/channels/TwilioOldModelBuilder';

const builder = new TwillioOldModelBuilder();
new ModelBuildDirector(builder);

export const TwilioOldModel = builder.model;
