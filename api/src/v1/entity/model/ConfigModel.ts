import { ConfigModelBuilder } from '../../builder/ConfigModelBuilder';
import { ModelBuildDirector } from '../../builder/ModelBuildDirector';

const builder = new ConfigModelBuilder();
new ModelBuildDirector(builder);

export const ConfigModel = builder.model;