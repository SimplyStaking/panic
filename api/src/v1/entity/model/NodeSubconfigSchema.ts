import { NodeSubconfigModelBuilder } from '../../builder/NodeSubconfigModelBuilder';
import { ModelBuildDirector } from '../../builder/ModelBuildDirector';

const builder = new NodeSubconfigModelBuilder();
new ModelBuildDirector(builder);

export const NodeSubconfigSchema = builder.schema;