import {TelegramModelBuilder} from '../../../builder/channels/TelegramModelBuilder';
import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';

const builder = new TelegramModelBuilder();
new ModelBuildDirector(builder);

export const TelegramModel = builder.model;
export const TelegramSchema = builder.schema;
