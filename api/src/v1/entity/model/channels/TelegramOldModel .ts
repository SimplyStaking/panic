import { TelegramOldModelBuilder }
    from '../../../builder/channels/TelegramOldModelBuilder';
import {ModelBuildDirector} from '../../../builder/ModelBuildDirector';

const builder = new TelegramOldModelBuilder();
new ModelBuildDirector(builder);

export const TelegramOldModel = builder.model;
