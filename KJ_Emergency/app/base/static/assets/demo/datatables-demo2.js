$(document).ready(function() {
  $('#dataTable2').DataTable({
    ajax: {url: "/admin-api/get-table-data2",
    type: "GET",
    dataSrc: ''
  },
    columns: [
      {data: "Name"},
      {data: "User_ID"},
      {data: "Heart_Rate"},
      {data: "Temperature"}.
      {data: "Humidity"},
    ]
  });
});
