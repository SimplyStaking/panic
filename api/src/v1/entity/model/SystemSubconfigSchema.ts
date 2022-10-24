import { SystemSubconfigModelBuilder }
    from '../../builder/SystemSubconfigModelBuilder';
import { ModelBuildDirector } from '../../builder/ModelBuildDirector';

const builder = new SystemSubconfigModelBuilder();
new ModelBuildDirector(builder);

export const SystemSubconfigSchema = builder.schema;