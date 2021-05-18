import React from 'react';
import PropTypes from 'prop-types';
import { forbidExtraProps } from 'airbnb-prop-types';
import {
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Box,
  Grid,
} from '@material-ui/core';
import Paper from '@material-ui/core/Paper';
import CheckIcon from '@material-ui/icons/Check';
import ClearIcon from '@material-ui/icons/Clear';
import CancelIcon from '@material-ui/icons/Cancel';
import StyledTableRow from 'assets/jss/custom-jss/StyledTableRow';
import StyledTableCell from 'assets/jss/custom-jss/StyledTableCell';
import { NEXT, BACK } from 'constants/constants';
import StepButtonContainer from 'containers/chains/common/stepButtonContainer';

const DockerTable = ({
  currentChain, config, dockerConfig, removeDockerDetails, data,
}) => {
  if (config.byId[currentChain].dockers.length === 0) {
    return (
      <div>
        <Box py={4}>
          <Grid container spacing={3} justify="center" alignItems="center">
            <Grid item xs={4} />
            <Grid item xs={2}>
              <StepButtonContainer
                disabled={false}
                text={BACK}
                navigation={data.dockerForm.backStep}
              />
            </Grid>
            <Grid item xs={2}>
              <StepButtonContainer
                disabled={false}
                text={NEXT}
                navigation={data.dockerForm.nextStep}
              />
            </Grid>
            <Grid item xs={4} />
          </Grid>
        </Box>
      </div>
    );
  }
  return (
    <Box pt={5}>
      <TableContainer component={Paper}>
        <Table className="table" aria-label="docker-table">
          <TableHead>
            <TableRow>
              <StyledTableCell align="center">Name</StyledTableCell>
              <StyledTableCell align="center">Monitor</StyledTableCell>
              <StyledTableCell align="center">Delete</StyledTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {config.byId[currentChain].dockers.map((id) => (
              <StyledTableRow key={id}>
                <StyledTableCell align="center">{dockerConfig.byId[id].name}</StyledTableCell>
                <StyledTableCell align="center">
                  {dockerConfig.byId[id].monitor_docker ? <CheckIcon /> : <ClearIcon />}
                </StyledTableCell>
                <StyledTableCell align="center">
                  <Button
                    onClick={() => {
                      removeDockerDetails({
                        id: dockerConfig.byId[id].id,
                        parent_id: currentChain,
                      });
                    }}
                  >
                    <CancelIcon />
                  </Button>
                </StyledTableCell>
              </StyledTableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Box py={4}>
        <Grid container spacing={3} justify="center" alignItems="center">
          <Grid item xs={4} />
          <Grid item xs={2}>
            <StepButtonContainer
              disabled={false}
              text={BACK}
              navigation={data.dockerForm.backStep}
            />
          </Grid>
          <Grid item xs={2}>
            <StepButtonContainer
              disabled={false}
              text={NEXT}
              navigation={data.dockerForm.nextStep}
            />
          </Grid>
          <Grid item xs={4} />
        </Grid>
      </Box>
    </Box>
  );
};

DockerTable.propTypes = forbidExtraProps({
  config: PropTypes.shape({
    byId: PropTypes.shape({
      dockers: PropTypes.arrayOf(PropTypes.string),
    }).isRequired,
  }).isRequired,
  dockerConfig: PropTypes.shape({
    byId: PropTypes.shape({
      id: PropTypes.string,
      parent_id: PropTypes.string,
      name: PropTypes.string,
      monitor_docker: PropTypes.bool,
    }).isRequired,
    allIds: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  removeDockerDetails: PropTypes.func.isRequired,
  currentChain: PropTypes.string.isRequired,
  data: PropTypes.shape({
    dockerForm: PropTypes.shape({
      backStep: PropTypes.string.isRequired,
      nextStep: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
});

export default DockerTable;
