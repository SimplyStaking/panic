import { ContractSubconfigModelBuilder }
    from '../../builder/ContractSubconfigModelBuilder';
import { ModelBuildDirector } from '../../builder/ModelBuildDirector';

const builder = new ContractSubconfigModelBuilder();
new ModelBuildDirector(builder);

export const ContractSubconfigSchema = builder.schema;