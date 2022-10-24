import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';
import {OpsgenieModelBuilder} from "../../../builder/channels/OpsgenieModelBuilder";

const builder = new OpsgenieModelBuilder();
new ModelBuildDirector(builder);

export const OpsgenieModel = builder.model;
export const OpsgenieSchema = builder.schema;
