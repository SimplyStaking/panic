import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';
import { OpsgenieOldModelBuilder } 
    from '../../../builder/channels/OpsgenieOldModelBuilder';

const builder = new OpsgenieOldModelBuilder();
new ModelBuildDirector(builder);

export const OpsgenieOldModel = builder.model;
