import { EVMNodeSubconfigModelBuilder }
    from '../../builder/EVMNodeSubconfigModelBuilder';
import { ModelBuildDirector } from '../../builder/ModelBuildDirector';

const builder = new EVMNodeSubconfigModelBuilder();
new ModelBuildDirector(builder);

export const EVMNodeSubconfigSchema = builder.schema;