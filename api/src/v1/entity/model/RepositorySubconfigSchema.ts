import { RepositorySubconfigModelBuilder }
    from '../../builder/RepositorySubconfigModelBuilder';
import { ModelBuildDirector } from '../../builder/ModelBuildDirector';

const builder = new RepositorySubconfigModelBuilder();
new ModelBuildDirector(builder);

export const RepositorySubconfigSchema = builder.schema;
