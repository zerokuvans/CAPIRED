const basicData = {
    columns: [{
        label: 'EMPLOYEES',
        field: 'employees',
        sort: true,
        width: 300,
        fixed: true
      },
      {
        label: 'POSITION',
        field: 'position',
        sort: false,
        width: 200
      },
      {
        label: 'START DATE',
        field: 'date',
        sort: false,
        width: 200,
      },
      {
        label: 'LAST ACTIVITY',
        field: 'activity',
        sort: false,
        width: 200
      },
      {
        label: 'CONTACTS',
        field: 'contacts',
        sort: true,
        width: 200
      },
      {
        label: 'AGE',
        field: 'Age',
        sort: false,
        width: 200,
      },
      {
        label: 'ADDRESS',
        field: 'address',
        sort: false,
        width: 200,
      },
      {
        label: 'SALARY',
        field: 'salary',
        sort: false,
        width: 200,
      },
    ],
    rows: [
      ['Tiger Nixon', 'System Architect', '2011/04/25', '2021/03/08', 'tnixon12@example.com', 61, 'Edinburgh', '$320,800'],
      ['Sonya Frost', 'Software Engineer', '2008/12/13', '2021/03/08', 'sfrost34@example.com', 23, 'Edinburgh', '$103,600'],
      ['Jena Gaines', 'Office Manager', '2008/12/19', '2021/03/08', 'jgaines75@example.com', 30, 'London', '$90,560'],
      ['Quinn Flynn', 'Support Lead', '2013/03/03', '2021/03/08', 'qflyn09@example.com',  22, 'Edinburgh', '$342,000'],
      ['Charde Marshall', 'Regional Director', '2008/10/16', '2021/03/08', 'cmarshall28@example.com', 36, 'San Francisco', '$470,600'],
      ['Haley Kennedy', 'Senior Marketing Designer', '2012/12/18', '2021/03/08', 'hkennedy63@example.com', 43, 'London', '$313,500'],
      ['Tatyana Fitzpatrick', 'Regional Director', '2010/03/17', '2021/03/08', 'tfitzpatrick00@example.com', 19, 'Warsaw', '$385,750'],
    ],
  };
  
  const datatable = document.getElementById('datatable');
  
  new mdb.Datatable(datatable, basicData);