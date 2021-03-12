import React from 'react';
import { Doughnut } from 'react-chartjs-2';

export interface DoughnutOverviewProps {

  labelList?: Array<string>;

  dataList?: Array<number>;

  backgroundColorList?: Array<string>;

  hoverBackgroundColorList?: Array<string>;

  labelPosition?: 'top' | 'bottom' | 'left' | 'right';

  linkTo: () => void;
}

export const DoughnutOverview: React.FC<DoughnutOverviewProps> = ({
  labelList,
  dataList,
  backgroundColorList,
  hoverBackgroundColorList,
  labelPosition,
  linkTo
}) => {

  return (
    <Doughnut
      data={{
        labels: labelList,
        datasets: [{
          data: dataList,
          backgroundColor: backgroundColorList,
          hoverBackgroundColor: hoverBackgroundColorList,
        }]
      }}
      options={{
        legend: {
          display: true,
          position: labelPosition,
          onClick: linkTo
        }
      }}
    />
  );
};