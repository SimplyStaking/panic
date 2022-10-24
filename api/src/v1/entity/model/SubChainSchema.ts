
import { ModelBuildDirector } from "../../builder/ModelBuildDirector";
import { SubChainModelBuilder } from "../../builder/SubChainModelBuilder";

const builder = new SubChainModelBuilder();
new ModelBuildDirector(builder);

export const SubChainSchema = builder.schema;
