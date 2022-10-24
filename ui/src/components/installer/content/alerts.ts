export const MORE_INFO_MESSAGES = [
  {
    title: "Info",
    messages: [
      `Alerts of this type have little to zero severity but consists of information which is still important to acknowledge. 
      Info alerts also include positive events. Example: System's storage usage is no longer at a critical level.`
    ]
  },
  {
    title: "Warning",
    messages: [
      `A less severe alert type but which still requires attention as it may be a warning of an incoming critical alert. 
      Example: System's storage usage reached 85%.`
    ]
  },
  {
    title: "Critical",
    messages: [
      `Alerts of this type are the most severe. Such alerts are raised to inform the node operator of a situation which 
      requires immediate action. Example: System's storage usage reached 100%.`
    ]
  },
  {
    title: "Error",
    messages: [
      `Alerts of this type are triggered by abnormal events and ranges from zero to high severity based on the error 
      that has occurred and how many times it is triggered. Example: Cannot access GitHub page alert.`
    ]
  }
];

export const MAIN_TEXT = `To simplify this process we have pre-configured the alerts based on our own experience with PANIC. 
You are free to change and adapt them as you see fit!`

export const SECONDARY_TEXT = `Make sure that warning thresholds and time windows are set lower than the critical thresholds 
and time windows, otherwise the alerter will not work properly.`

export const THIRD_TEXT = `PANIC supports four types of alerts:`

export const ALERT_THRESHOLD_TABLE_HEADERS = [
  {
    title: "Alert",
    sortable: false
  },
  {
    title: "Warning Threshold",
    sortable: false
  },
  {
    title: "Critical Threshold",
    sortable: false
  },
  {
    title: "Enabled",
    sortable: false
  },
];

export const ALERT_SEVERITY_TABLE_HEADERS = [
  {
    title: "Alert",
    sortable: false
  },
  {
    title: "Severity",
    sortable: false
  },
  {
    title: "Enabled",
    sortable: false
  }
];