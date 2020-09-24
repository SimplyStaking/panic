import * as Yup from 'yup';

const NodeSchema = (props) => Yup.object().shape({
  cosmosNodeName: Yup.string()
    .test(
      'unique-node-name',
      'Node name is not unique.',
      (value) => {
        const { nodesConfig } = props;
        if (nodesConfig.allIds.length === 0) {
          return true;
        }
        for (let i = 0; i < nodesConfig.allIds.length; i += 1) {
          if (nodesConfig.byId[nodesConfig.allIds[i]].cosmosNodeName === value) {
            return false;
          }
        }
        return true;
      },
    )
    .required('Node name is required.'),
});

export default NodeSchema;
