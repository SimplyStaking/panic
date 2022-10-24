import { BaseChainModelBuilder } from '../../builder/BaseChainModelBuilder';
import { ModelBuildDirector } from '../../builder/ModelBuildDirector';

const builder = new BaseChainModelBuilder();
new ModelBuildDirector(builder);

export const BaseChainModel = builder.model;
export const BaseChainSchema = builder.schema;