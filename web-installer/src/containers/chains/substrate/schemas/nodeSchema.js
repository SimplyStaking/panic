import * as Yup from 'yup';

const NodeSchema = (props) => Yup.object().shape({
  cosmosNodeName: Yup.string()
    .test(
      'unique-node-name',
      'Node name is not unique.',
      (value) => {
        const { substrateConfigs } = props;
        if (substrateConfigs.length === 0) {
          return true;
        }
        for (let i = 0; i < substrateConfigs.length; i += 1) {
          if (substrateConfigs[i].nodes.length === 0) {
            return true;
          }
          for (let j = 0; j < substrateConfigs[i].nodes.length; j += 1) {
            if (substrateConfigs[i].nodes[j].cosmosNodeName === value) {
              return false;
            }
          }
        }
        return true;
      },
    )
    .required('Node name is required.'),
});

export default NodeSchema;
