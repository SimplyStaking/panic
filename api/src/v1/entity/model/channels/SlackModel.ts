import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';
import {SlackModelBuilder} from "../../../builder/channels/SlackModelBuilder";

const builder = new SlackModelBuilder();
new ModelBuildDirector(builder);

export const SlackModel = builder.model;
export const SlackSchema = builder.schema;
