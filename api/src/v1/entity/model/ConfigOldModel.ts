import { ConfigOldModelBuilder } from '../../builder/ConfigOldModelBuilder';
import { ModelBuildDirector } from '../../builder/ModelBuildDirector';

const builder = new ConfigOldModelBuilder();
new ModelBuildDirector(builder);

export const ConfigOldModel = builder.model;