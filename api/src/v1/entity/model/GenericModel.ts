import {GenericModelBuilder} from '../../builder/GenericModelBuilder';
import {ModelBuildDirector} from '../../builder/ModelBuildDirector';

const builder = new GenericModelBuilder();
new ModelBuildDirector(builder);

export const GenericModel = builder.model;
export const GenericSchema = builder.schema;
